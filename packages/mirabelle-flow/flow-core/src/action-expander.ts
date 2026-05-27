import type { FlowNode } from '@mirabelle/flow-shared'
import { getHaBlockDescriptor } from './ha-block-registry.js'
import { isHaConditionItem } from './ha-item-classifier.js'

export interface ActionBuildContext {
  nodes: FlowNode[]
  edges: import('@mirabelle/flow-shared').FlowEdge[]
  addNode: (
    path: string,
    kind: import('@mirabelle/flow-shared').FlowNodeKind,
    label: string,
    data: Record<string, unknown>,
    parentId?: string,
  ) => FlowNode
  connect: (
    source: FlowNode,
    target: FlowNode,
    options?: {
      label?: string
      branch?: string
      edgeKind?: import('@mirabelle/flow-shared').FlowEdgeKind
      sourceHandle?: string
      targetHandle?: string
      itemKey?: string
    },
  ) => void
}

export type ExpandBranchSequenceFn = (
  ctx: ActionBuildContext,
  actions: unknown[],
  anchor: FlowNode,
  pathPrefix: string,
  branchKey: string,
) => FlowNode[]

export function summarizeCondition(c: Record<string, unknown>): string {
  const cond = c.condition as string | undefined
  if (cond === 'trigger' && typeof c.id === 'string') {
    return `Trigger: ${c.id}`
  }
  if (cond === 'template' && typeof c.value_template === 'string') {
    const t = c.value_template
    return t.length > 48 ? `Template: ${t.slice(0, 48)}…` : `Template: ${t}`
  }
  if (cond === 'state') {
    const entity = c.entity_id ?? ''
    const state = c.state
    const stateStr = Array.isArray(state) ? state.join(', ') : String(state ?? '')
    return stateStr ? `State: ${entity} = ${stateStr}` : `State: ${entity}`
  }
  if (cond === 'numeric_state') {
    return `Numeric: ${String(c.entity_id ?? '')}`
  }
  if (cond === 'time') {
    return 'Time window'
  }
  if (cond === 'zone') {
    return `Zone: ${String(c.entity_id ?? '')}`
  }
  return cond ? `Condition: ${cond}` : 'Condition'
}

const SERVICE_LABEL_MAX = 96

function truncateLabel(text: string, max = SERVICE_LABEL_MAX): string {
  return text.length > max ? `${text.slice(0, max)}…` : text
}

function summarizeDataPayload(data: Record<string, unknown>): string | undefined {
  const entries = Object.entries(data).filter(([k]) => k !== 'entity_id')
  if (entries.length === 0) {
    return undefined
  }
  const preview = entries
    .slice(0, 2)
    .map(([k, v]) => {
      if (typeof v === 'string') {
        const t = v.length > 32 ? `${v.slice(0, 32)}…` : v
        return `${k}=${t}`
      }
      return `${k}=${JSON.stringify(v)}`
    })
    .join(', ')
  return entries.length > 2 ? `${preview}, …` : preview
}

export function summarizeServiceAction(a: Record<string, unknown>): string {
  const service = String(a.service ?? 'Action')
  const target = a.target as { entity_id?: string | string[] } | undefined
  let entity: string | undefined
  if (typeof target?.entity_id === 'string') {
    entity = target.entity_id
  }
  else if (Array.isArray(target?.entity_id)) {
    entity = target.entity_id.join(', ')
  }
  const data = a.data as Record<string, unknown> | undefined
  const dataSummary = data ? summarizeDataPayload(data) : undefined
  if (entity && dataSummary) {
    return truncateLabel(`${service} → ${entity} (${dataSummary})`)
  }
  if (entity) {
    return truncateLabel(`${service} → ${entity}`)
  }
  if (dataSummary) {
    return truncateLabel(`${service} (${dataSummary})`)
  }
  return service
}

/** Condition nodes nested inside a container (choose, if, …). */
export function buildConditionsInContainer(
  ctx: ActionBuildContext,
  conditions: unknown[],
  container: FlowNode,
  pathPrefix: string,
  options: { branchKey?: string, branchIndex?: number } = {},
): FlowNode[] {
  const branchIndex = options.branchIndex ?? 0
  const validConditions = conditions.filter(
    c => !!c && typeof c === 'object' && isHaConditionItem(c as Record<string, unknown>),
  ) as Record<string, unknown>[]
  if (validConditions.length === 0) {
    return []
  }

  const group = ctx.addNode(
    pathPrefix,
    'ha_block',
    'Conditions',
    {
      blockKey: 'conditions',
      isContainer: true,
      conditionOperator: 'and',
      branchKey: options.branchKey,
      layoutOrder: branchIndex * 100,
    },
    container.id,
  )

  const conditionNodes: FlowNode[] = []
  let prev: FlowNode | undefined

  validConditions.forEach((c, i) => {
    const node = ctx.addNode(
      `${pathPrefix}/${i}`,
      'condition',
      summarizeCondition(c),
      {
        ...c,
        branchKey: options.branchKey,
        layoutOrder: branchIndex * 100 + i + 1,
      },
      group.id,
    )

    if (prev) {
      ctx.connect(prev, node)
    }
    else {
      ctx.connect(group, node)
    }

    conditionNodes.push(node)
    prev = node
  })

  return conditionNodes.length > 0 ? [group] : []
}

/** Service call as a single action node (target/data summarized in the label). */
export function expandServiceAction(
  ctx: ActionBuildContext,
  a: Record<string, unknown>,
  path: string,
  options: {
    parentId?: string
    prev?: FlowNode
  } = {},
): FlowNode {
  const main = ctx.addNode(
    path,
    'action',
    summarizeServiceAction(a),
    { ...a, blockKey: 'service' },
    options.parentId,
  )
  if (options.prev) {
    ctx.connect(options.prev, main)
  }
  return main
}

/** Service inside a HA container (repeat, parallel, …). */
export function expandServiceActionInContainer(
  ctx: ActionBuildContext,
  a: Record<string, unknown>,
  path: string,
  container: FlowNode,
  prev: FlowNode | undefined,
): FlowNode {
  return expandServiceAction(ctx, a, path, { parentId: container.id, prev })
}

export interface ChooseBranch {
  conditions?: unknown[]
  sequence?: unknown[]
}

function isIfBranchList(ifList: unknown[]): boolean {
  return ifList.some(
    item =>
      item !== null
      && typeof item === 'object'
      && ('conditions' in item || 'sequence' in item),
  )
}

/** HA supports branch-list `if` and condition-list `if` + `then` / `else`. */
export function parseIfActionShape(a: Record<string, unknown>): {
  mode: 'branches' | 'then_else'
  branches: ChooseBranch[]
  conditions: unknown[]
  thenSeq: unknown[]
  elseSeq: unknown[]
} {
  const ifList = Array.isArray(a.if) ? a.if : []
  const thenSeq = Array.isArray(a.then) ? a.then : []
  const elseSeq = Array.isArray(a.else) ? a.else : []

  if (isIfBranchList(ifList)) {
    return {
      mode: 'branches',
      branches: ifList as ChooseBranch[],
      conditions: [],
      thenSeq: [],
      elseSeq: elseSeq,
    }
  }

  return {
    mode: 'then_else',
    branches: [],
    conditions: ifList,
    thenSeq,
    elseSeq,
  }
}

export function summarizeHaBlock(a: Record<string, unknown>): string {
  const descriptor = getHaBlockDescriptor(a)
  if (descriptor.key === 'service') {
    return summarizeServiceAction(a)
  }
  return descriptor.summary(a)
}

/**
 * Choose container: conditions (+ Default marker) as first-level children only.
 * Branch sequences are built outside the choose parent via expandBranchSequence.
 */
export function materializeChoose(
  ctx: ActionBuildContext,
  a: Record<string, unknown>,
  path: string,
  options: {
    parentId?: string
    flowParent?: FlowNode
    prev?: FlowNode
    firstEdge?: {
      sourceHandle?: string
      targetHandle?: string
      label?: string
      branch?: string
      itemKey?: string
    }
  },
  expandBranchSequence: ExpandBranchSequenceFn,
): FlowNode {
  const choose = (Array.isArray(a.choose) ? a.choose : []) as ChooseBranch[]
  const defaultSeq = (a as { default?: unknown[] }).default ?? []
  const optionDefs = choose.map((branch, bi) => ({
    key: `opt-${bi}`,
    label: `Option ${bi + 1}`,
    conditions: branch.conditions ?? [],
    hasSequence: (branch.sequence ?? []).length > 0,
  }))
  if (defaultSeq.length > 0) {
    optionDefs.push({
      key: 'opt-default',
      label: 'Default',
      conditions: [],
      hasSequence: true,
    })
  }

  const chooseNode = ctx.addNode(
    path,
    'choose',
    'Choose',
    {
      options: optionDefs,
      isContainer: true,
      layoutHeaderHeight: 40,
      hasDefault: defaultSeq.length > 0,
    },
    options.parentId,
  )
  if (options.prev) {
    ctx.connect(options.prev, chooseNode)
  }
  else if (options.flowParent) {
    ctx.connect(options.flowParent, chooseNode, options.firstEdge)
  }

  choose.forEach((branch, bi) => {
    const optionKey = `opt-${bi}`
    buildConditionsInContainer(
      ctx,
      branch.conditions ?? [],
      chooseNode,
      `${path}/choose/${bi}/conditions`,
      { branchKey: optionKey, branchIndex: bi },
    )
  })

  if (defaultSeq.length > 0) {
    ctx.addNode(
      `${path}/choose/default/marker`,
      'choose_option',
      'Default',
      {
        key: 'opt-default',
        label: 'Default',
        isDefault: true,
        layoutOrder: 9000,
      },
      chooseNode.id,
    )
  }

  const branchLeaves: FlowNode[] = []
  choose.forEach((branch, bi) => {
    const optionKey = `opt-${bi}`
    const seq = branch.sequence ?? []
    if (seq.length > 0) {
      const leaves = expandBranchSequence(
        ctx,
        seq,
        chooseNode,
        `${path}/choose/${bi}/sequence`,
        optionKey,
      )
      if (leaves.length > 0) {
        branchLeaves.push(leaves[leaves.length - 1]!)
      }
    }
  })

  if (defaultSeq.length > 0) {
    const defLeaves = expandBranchSequence(
      ctx,
      defaultSeq,
      chooseNode,
      `${path}/choose/default/sequence`,
      'opt-default',
    )
    if (defLeaves.length > 0) {
      branchLeaves.push(defLeaves[defLeaves.length - 1]!)
    }
  }

  return branchLeaves[branchLeaves.length - 1] ?? chooseNode
}

export function materializeIf(
  ctx: ActionBuildContext,
  a: Record<string, unknown>,
  path: string,
  options: {
    parentId?: string
    flowParent?: FlowNode
    prev?: FlowNode
    firstEdge?: {
      sourceHandle?: string
      targetHandle?: string
      label?: string
      branch?: string
      itemKey?: string
    }
  },
  expandBranchSequence: ExpandBranchSequenceFn,
): FlowNode {
  const shape = parseIfActionShape(a)
  const branchCount =
    shape.mode === 'branches' ? shape.branches.length : shape.conditions.length > 0 ? 1 : 0
  const ifNode = ctx.addNode(
    path,
    'ha_block',
    'If',
    {
      blockKey: 'if',
      isContainer: true,
      layoutHeaderHeight: 40,
      branchCount,
      hasDefault: shape.elseSeq.length > 0,
      ifShape: shape.mode,
    },
    options.parentId,
  )
  if (options.prev) {
    ctx.connect(options.prev, ifNode)
  }
  else if (options.flowParent) {
    ctx.connect(options.flowParent, ifNode, options.firstEdge)
  }

  const leaves: FlowNode[] = []

  if (shape.mode === 'then_else') {
    if (shape.conditions.length > 0) {
      buildConditionsInContainer(
        ctx,
        shape.conditions,
        ifNode,
        `${path}/if/conditions`,
        { branchKey: 'if-0', branchIndex: 0 },
      )
    }

    if (shape.thenSeq.length > 0) {
      const thenLeaves = expandBranchSequence(
        ctx,
        shape.thenSeq,
        ifNode,
        `${path}/if/then/sequence`,
        'if-0',
      )
      if (thenLeaves.length > 0) {
        leaves.push(thenLeaves[thenLeaves.length - 1]!)
      }
    }
  }
  else {
    shape.branches.forEach((branch, bi) => {
      buildConditionsInContainer(
        ctx,
        branch.conditions ?? [],
        ifNode,
        `${path}/if/${bi}/conditions`,
        { branchKey: `if-${bi}`, branchIndex: bi },
      )
    })

    shape.branches.forEach((branch, bi) => {
      const seq = branch.sequence ?? []
      if (seq.length > 0) {
        const branchLeaves = expandBranchSequence(
          ctx,
          seq,
          ifNode,
          `${path}/if/${bi}/sequence`,
          `if-${bi}`,
        )
        if (branchLeaves.length > 0) {
          leaves.push(branchLeaves[branchLeaves.length - 1]!)
        }
      }
    })
  }

  if (shape.elseSeq.length > 0) {
    ctx.addNode(
      `${path}/if/else/marker`,
      'choose_option',
      'Else',
      { key: 'if-else', label: 'Else', isDefault: true, layoutOrder: 9000 },
      ifNode.id,
    )
    const elseLeaves = expandBranchSequence(
      ctx,
      shape.elseSeq,
      ifNode,
      `${path}/if/else/sequence`,
      'if-else',
    )
    if (elseLeaves.length > 0) {
      leaves.push(elseLeaves[elseLeaves.length - 1]!)
    }
  }

  return leaves[leaves.length - 1] ?? ifNode
}
