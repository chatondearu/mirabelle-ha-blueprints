import type { FlowNode } from '@mirabelle/flow-shared'
import { getHaBlockDescriptor } from './ha-block-registry.js'

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
  const dataKeys = data ? Object.keys(data).filter(k => k !== 'entity_id') : []
  if (entity && dataKeys.length > 0) {
    return `${service} → ${entity} (${dataKeys.slice(0, 2).join(', ')}…)`
  }
  if (entity) {
    return `${service} → ${entity}`
  }
  if (dataKeys.length > 0) {
    return `${service} (${dataKeys.join(', ')})`
  }
  return service
}

function formatDetailLabel(part: string, value: unknown): string | null {
  if (value === undefined || value === null) {
    return null
  }
  if (part === 'target' && typeof value === 'object') {
    const t = value as { entity_id?: string | string[]; device_id?: string }
    if (typeof t.entity_id === 'string') {
      return `target: ${t.entity_id}`
    }
    if (Array.isArray(t.entity_id)) {
      return `target: ${t.entity_id.join(', ')}`
    }
    if (t.device_id) {
      return `target: device ${t.device_id}`
    }
    return `target: ${JSON.stringify(value)}`
  }
  if (part === 'data' && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (entries.length === 0) {
      return null
    }
    const preview = entries
      .slice(0, 3)
      .map(([k, v]) => `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`)
      .join(', ')
    return entries.length > 3 ? `data: ${preview}…` : `data: ${preview}`
  }
  if (typeof value === 'string') {
    return `${part}: ${value.length > 40 ? `${value.slice(0, 40)}…` : value}`
  }
  return `${part}: ${JSON.stringify(value)}`
}

/** Condition nodes nested inside a container (choose, if, …). */
export function buildConditionsInContainer(
  ctx: ActionBuildContext,
  conditions: unknown[],
  container: FlowNode,
  pathPrefix: string,
  options: { branchKey?: string, branchIndex?: number } = {},
): FlowNode[] {
  const nodes: FlowNode[] = []
  const branchIndex = options.branchIndex ?? 0
  conditions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const c = raw as Record<string, unknown>
    const node = ctx.addNode(
      `${pathPrefix}/${i}`,
      'condition',
      summarizeCondition(c),
      {
        ...c,
        branchKey: options.branchKey,
        layoutOrder: branchIndex * 100 + i,
      },
      container.id,
    )
    nodes.push(node)
  })
  return nodes
}

/** Service call with target/data as first-level children only (under the action node). */
export function expandServiceActionInContainer(
  ctx: ActionBuildContext,
  a: Record<string, unknown>,
  path: string,
  container: FlowNode,
  prev: FlowNode | undefined,
): FlowNode {
  const main = ctx.addNode(
    path,
    'action',
    summarizeServiceAction(a),
    { ...a, blockKey: 'service' },
    container.id,
  )
  if (prev) {
    ctx.connect(prev, main)
  }

  let detailIndex = 0
  let hasDetails = false
  if (a.target !== undefined) {
    const label = formatDetailLabel('target', a.target)
    if (label) {
      hasDetails = true
      ctx.addNode(
        `${path}/detail/${detailIndex++}`,
        'ha_block',
        label,
        { part: 'target', value: a.target },
        main.id,
      )
    }
  }
  if (a.data !== undefined) {
    const label = formatDetailLabel('data', a.data)
    if (label) {
      hasDetails = true
      ctx.addNode(
        `${path}/detail/${detailIndex++}`,
        'ha_block',
        label,
        { part: 'data', value: a.data },
        main.id,
      )
    }
  }
  if (hasDetails) {
    main.data.isContainer = true
    main.data.layoutHeaderHeight = 44
  }

  return main
}

export interface ChooseBranch {
  conditions?: unknown[]
  sequence?: unknown[]
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
  const branches = (Array.isArray(a.if) ? a.if : []) as ChooseBranch[]
  const elseSeq = (a as { else?: unknown[] }).else ?? []
  const ifNode = ctx.addNode(
    path,
    'ha_block',
    'If',
    {
      blockKey: 'if',
      isContainer: true,
      layoutHeaderHeight: 40,
      branchCount: branches.length,
      hasDefault: elseSeq.length > 0,
    },
    options.parentId,
  )
  if (options.prev) {
    ctx.connect(options.prev, ifNode)
  }
  else if (options.flowParent) {
    ctx.connect(options.flowParent, ifNode, options.firstEdge)
  }

  branches.forEach((branch, bi) => {
    buildConditionsInContainer(
      ctx,
      branch.conditions ?? [],
      ifNode,
      `${path}/if/${bi}/conditions`,
      { branchKey: `if-${bi}`, branchIndex: bi },
    )
  })

  if (elseSeq.length > 0) {
    ctx.addNode(
      `${path}/if/else/marker`,
      'choose_option',
      'Else',
      { key: 'if-else', label: 'Else', isDefault: true, layoutOrder: 9000 },
      ifNode.id,
    )
  }

  const leaves: FlowNode[] = []
  branches.forEach((branch, bi) => {
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

  if (elseSeq.length > 0) {
    const elseLeaves = expandBranchSequence(
      ctx,
      elseSeq,
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
