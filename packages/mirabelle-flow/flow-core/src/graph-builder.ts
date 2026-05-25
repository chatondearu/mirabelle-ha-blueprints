import type {
  BlueprintMeta,
  FlowDocument,
  FlowEdge,
  FlowEdgeKind,
  FlowListItem,
  FlowNode,
  FlowNodeKind,
  FlowViewMode,
} from '@mirabelle/flow-shared'
import { FLOW_LAYOUT, getNodeLayer, isConfigLayerNode } from '@mirabelle/flow-shared'
import { getHaBlockDescriptor } from './ha-block-registry.js'
import { extractTriggerIdsFromCondition } from './trigger-path.js'

interface BuildContext {
  nodes: FlowNode[]
  edges: FlowEdge[]
  edgeCounter: number
}

function nextEdgeId(ctx: BuildContext): string {
  ctx.edgeCounter += 1
  return `e-${ctx.edgeCounter}`
}

function addNode(
  ctx: BuildContext,
  path: string,
  kind: FlowNodeKind,
  label: string,
  data: Record<string, unknown>,
  parentId?: string,
): FlowNode {
  const id = path.replace(/\//g, '_') || 'node'
  const node: FlowNode = {
    id,
    kind,
    label,
    path,
    data,
    parentId,
    layer: getNodeLayer(kind),
  }
  ctx.nodes.push(node)
  return node
}

function connect(
  ctx: BuildContext,
  source: FlowNode,
  target: FlowNode,
  options: {
    label?: string
    branch?: string
    edgeKind?: FlowEdgeKind
    sourceHandle?: string
    targetHandle?: string
    itemKey?: string
  } = {},
): void {
  const edgeKind = options.edgeKind ?? 'flow'
  const exists = ctx.edges.some(
    e =>
      e.source === source.id
      && e.target === target.id
      && e.edgeKind === edgeKind
      && e.label === options.label
      && e.sourceHandle === options.sourceHandle
      && e.targetHandle === options.targetHandle,
  )
  if (exists) {
    return
  }
  ctx.edges.push({
    id: nextEdgeId(ctx),
    source: source.id,
    target: target.id,
    label: options.label,
    branch: options.branch,
    edgeKind,
    sourceHandle: options.sourceHandle,
    targetHandle: options.targetHandle,
    itemKey: options.itemKey,
  })
}

function summarizeTrigger(t: Record<string, unknown>): string {
  const platform = (t.platform ?? t.trigger) as string | undefined
  const entity = t.entity_id as string | undefined
  const id = typeof t.id === 'string' ? t.id : undefined
  if (platform && entity) {
    return id ? `Trigger: ${platform} (${entity}) [${id}]` : `Trigger: ${platform} (${entity})`
  }
  if (platform) {
    return id ? `Trigger: ${platform} [${id}]` : `Trigger: ${platform}`
  }
  return id ? `Trigger [${id}]` : 'Trigger'
}

function summarizeCondition(c: Record<string, unknown>): string {
  const cond = c.condition as string | undefined
  if (cond === 'trigger' && typeof c.id === 'string') {
    return `Trigger: ${c.id}`
  }
  if (cond === 'template' && typeof c.value_template === 'string') {
    const t = c.value_template
    return t.length > 40 ? `Template: ${t.slice(0, 40)}…` : `Template: ${t}`
  }
  if (cond === 'state') {
    return `State: ${String(c.entity_id ?? '')}`
  }
  return cond ? `Condition: ${cond}` : 'Condition'
}

function summarizeAction(a: Record<string, unknown>): string {
  const descriptor = getHaBlockDescriptor(a)
  if (typeof a.service === 'string') {
    return a.service
  }
  if (a.choose) {
    return 'Choose'
  }
  if (a.delay) {
    return `Delay: ${JSON.stringify(a.delay)}`
  }
  if (a.wait_template) {
    return 'Wait template'
  }
  if (a.repeat) {
    return 'Repeat'
  }
  if (a.parallel) {
    return 'Parallel'
  }
  if (a.sequence) {
    return 'Sequence'
  }
  return descriptor.summary(a)
}

function buildTriggers(
  ctx: BuildContext,
  triggers: unknown[],
  parent?: FlowNode,
): FlowNode[] {
  const nodes: FlowNode[] = []
  triggers.forEach((t, i) => {
    if (!t || typeof t !== 'object') {
      return
    }
    const path = `trigger/${i}`
    const node = addNode(
      ctx,
      path,
      'trigger',
      summarizeTrigger(t as Record<string, unknown>),
      t as Record<string, unknown>,
      parent?.id,
    )
    if (parent) {
      connect(ctx, parent, node)
    }
    nodes.push(node)
  })
  return nodes
}

function buildConditions(
  ctx: BuildContext,
  conditions: unknown[],
  parent: FlowNode,
): FlowNode[] {
  const leaves: FlowNode[] = []
  conditions.forEach((c, i) => {
    if (!c || typeof c !== 'object') {
      return
    }
    const path = `condition/${i}`
    const node = addNode(
      ctx,
      path,
      'condition',
      summarizeCondition(c as Record<string, unknown>),
      c as Record<string, unknown>,
      undefined,
    )
    connect(ctx, parent, node)
    leaves.push(node)
  })
  return leaves
}

function valueType(value: unknown): string {
  if (Array.isArray(value)) {
    return 'array'
  }
  if (value === null) {
    return 'null'
  }
  return typeof value
}

function buildBlueprintGroup(
  ctx: BuildContext,
  meta: BlueprintMeta,
  inputItems: FlowListItem[],
  simulationValues: Record<string, unknown>,
): FlowNode {
  const parent = addNode(
    ctx,
    'blueprint',
    'blueprint',
    meta.name ?? 'Blueprint',
    {
      meta,
      inputs: meta.inputs,
      simulationValues,
      isGroup: true,
    },
    undefined,
  )
  for (const item of inputItems) {
    addNode(
      ctx,
      `blueprint/input/${item.key}`,
      'blueprint_input',
      item.label,
      {
        key: item.key,
        value: item.value,
        valueType: item.valueType,
        meta: item.meta,
        selector: item.meta?.selector,
      },
      parent.id,
    )
  }
  return parent
}

function buildVariablesGroup(
  ctx: BuildContext,
  variables: Record<string, unknown>,
): FlowNode | null {
  const entries = Object.entries(variables)
  if (entries.length === 0) {
    return null
  }
  const parent = addNode(
    ctx,
    'variables',
    'variables',
    'Variables',
    { isGroup: true },
    undefined,
  )
  for (const [name, value] of entries) {
    addNode(
      ctx,
      `variables/${name}`,
      'variable',
      name,
      { name, value, key: name },
      parent.id,
    )
  }
  return parent
}

function expandActionItem(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
  parent: FlowNode,
  prev: FlowNode | undefined,
  firstEdge?: {
    sourceHandle?: string
    targetHandle?: string
    label?: string
    branch?: string
    itemKey?: string
  },
): FlowNode {
  if (Array.isArray(a.sequence)) {
    const seqNode = addNode(
      ctx,
      path,
      'sequence',
      'Sequence',
      { sequence: true, isContainer: true },
      undefined,
    )
    if (prev) {
      connect(ctx, prev, seqNode)
    }
    else {
      connect(ctx, parent, seqNode, firstEdge)
    }
    const leaves = buildActionsInContainer(ctx, a.sequence, seqNode, `${path}/sequence`)
    return leaves[leaves.length - 1] ?? seqNode
  }

  if (a.repeat && typeof a.repeat === 'object') {
    const repeatNode = addNode(ctx, path, 'repeat', 'Repeat', { ...a, isContainer: true }, undefined)
    if (prev) {
      connect(ctx, prev, repeatNode)
    }
    else {
      connect(ctx, parent, repeatNode, firstEdge)
    }
    const body = (a.repeat as { sequence?: unknown[] }).sequence ?? []
    if (body.length > 0) {
      const leaves = buildActionsInContainer(ctx, body, repeatNode, `${path}/repeat/sequence`)
      return leaves[leaves.length - 1] ?? repeatNode
    }
    return repeatNode
  }

  if (Array.isArray(a.parallel)) {
    const parNode = addNode(
      ctx,
      path,
      'parallel',
      'Parallel',
      { parallel: true, isContainer: true },
      undefined,
    )
    if (prev) {
      connect(ctx, prev, parNode)
    }
    else {
      connect(ctx, parent, parNode, firstEdge)
    }
    let last: FlowNode = parNode
    a.parallel.forEach((branch, bi) => {
      if (branch && typeof branch === 'object') {
        const leaves = buildActionsInContainer(
          ctx,
          [branch],
          parNode,
          `${path}/parallel/${bi}`,
        )
        if (leaves.length > 0) {
          last = leaves[leaves.length - 1]!
        }
      }
    })
    return last
  }

  if (a.delay !== undefined) {
    const delayNode = addNode(
      ctx,
      path,
      'delay',
      summarizeAction(a),
      a,
      undefined,
    )
    if (prev) {
      connect(ctx, prev, delayNode)
    }
    else {
      connect(ctx, parent, delayNode, firstEdge)
    }
    return delayNode
  }

  if (a.wait_template !== undefined || a.wait_for_trigger !== undefined) {
    const waitNode = addNode(ctx, path, 'wait', summarizeAction(a), a, undefined)
    if (prev) {
      connect(ctx, prev, waitNode)
    }
    else {
      connect(ctx, parent, waitNode, firstEdge)
    }
    return waitNode
  }

  const node = addNode(ctx, path, 'action', summarizeAction(a), a, undefined)
  if (prev) {
    connect(ctx, prev, node)
  }
  else {
    connect(ctx, parent, node, firstEdge)
  }
  return node
}

/** Top-level action chain when no trigger/condition anchor exists (e.g. script blueprints). */
function buildRootActionChain(
  ctx: BuildContext,
  actions: unknown[],
  pathPrefix: string,
): void {
  let prev: FlowNode | undefined
  actions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const a = raw as Record<string, unknown>
    const path = `${pathPrefix}/${i}`
    if (!prev) {
      prev = expandActionItemRoot(ctx, a, path)
    }
    else {
      prev = expandActionItem(ctx, a, path, prev, prev)
    }
  })
}

function expandActionItemRoot(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
): FlowNode {
  if (a.choose) {
    return materializeChoose(ctx, a, path, {})
  }

  if (Array.isArray(a.sequence)) {
    const seqNode = addNode(
      ctx,
      path,
      'sequence',
      'Sequence',
      { sequence: true, isContainer: true },
      undefined,
    )
    const leaves = buildActionsInContainer(ctx, a.sequence, seqNode, `${path}/sequence`)
    return leaves[leaves.length - 1] ?? seqNode
  }
  const descriptor = getHaBlockDescriptor(a)
  return addNode(ctx, path, descriptor.nodeKind, summarizeAction(a), a, undefined)
}

/** Actions nested inside a container node (sequence, parallel, repeat, choose branches). */
function buildActionsInContainer(
  ctx: BuildContext,
  actions: unknown[],
  container: FlowNode,
  pathPrefix: string,
): FlowNode[] {
  const leaves: FlowNode[] = []
  let prev: FlowNode | undefined

  actions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const a = raw as Record<string, unknown>
    const path = `${pathPrefix}/${i}`
    const node = expandActionItemInContainer(ctx, a, path, container, prev)
    prev = node
    leaves.push(node)
  })

  return leaves
}

function materializeChoose(
  ctx: BuildContext,
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
): FlowNode {
  const choose = a.choose as Array<{
    conditions?: unknown[]
    sequence?: unknown[]
  }>
  const optionDefs = choose.map((branch, bi) => ({
    key: `opt-${bi}`,
    label: `Option ${bi + 1}`,
    conditions: branch.conditions ?? [],
    hasSequence: (branch.sequence ?? []).length > 0,
  }))
  const chooseNode = addNode(
    ctx,
    path,
    'choose',
    'Choose',
    {
      options: optionDefs,
      isContainer: true,
      hasDefault: Array.isArray((a as { default?: unknown[] }).default)
        && ((a as { default?: unknown[] }).default?.length ?? 0) > 0,
    },
    options.parentId,
  )
  if (options.prev) {
    connect(ctx, options.prev, chooseNode)
  }
  else if (options.flowParent) {
    connect(ctx, options.flowParent, chooseNode, options.firstEdge)
  }

  choose.forEach((branch, bi) => {
    const optionKey = `opt-${bi}`
    addNode(
      ctx,
      `${path}/choose/${bi}/option`,
      'choose_option',
      `Option ${bi + 1}`,
      {
        key: optionKey,
        label: `Option ${bi + 1}`,
        conditions: branch.conditions ?? [],
      },
      chooseNode.id,
    )
  })

  const branchLeaves: FlowNode[] = []
  choose.forEach((branch, bi) => {
    const branchPath = `${path}/choose/${bi}`
    const seq = branch.sequence ?? []
    const seqLeaves = buildActionsInContainer(
      ctx,
      seq,
      chooseNode,
      `${branchPath}/sequence`,
    )
    if (seqLeaves.length > 0) {
      branchLeaves.push(seqLeaves[seqLeaves.length - 1]!)
    }
  })

  const defaultSeq = (a as { default?: unknown[] }).default ?? []
  if (defaultSeq.length > 0) {
    addNode(
      ctx,
      `${path}/choose/default/option`,
      'choose_option',
      'Default',
      { key: 'opt-default', label: 'Default', conditions: [] },
      chooseNode.id,
    )
    const defLeaves = buildActionsInContainer(ctx, defaultSeq, chooseNode, `${path}/default`)
    branchLeaves.push(...defLeaves)
  }

  return branchLeaves[branchLeaves.length - 1] ?? chooseNode
}

function expandActionItemInContainer(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
  container: FlowNode,
  prev: FlowNode | undefined,
): FlowNode {
  if (a.choose) {
    return materializeChoose(ctx, a, path, { parentId: container.id, prev })
  }

  if (Array.isArray(a.sequence)) {
    const seqNode = addNode(
      ctx,
      path,
      'sequence',
      'Sequence',
      { sequence: true, isContainer: true },
      container.id,
    )
    if (prev) {
      connect(ctx, prev, seqNode)
    }
    const leaves = buildActionsInContainer(ctx, a.sequence, seqNode, `${path}/sequence`)
    return leaves[leaves.length - 1] ?? seqNode
  }

  const descriptor = getHaBlockDescriptor(a)
  const node = addNode(
    ctx,
    path,
    descriptor.nodeKind,
    summarizeAction(a),
    a,
    container.id,
  )
  if (prev) {
    connect(ctx, prev, node)
  }
  return node
}

function buildActions(
  ctx: BuildContext,
  actions: unknown[],
  parent: FlowNode,
  pathPrefix: string,
  firstEdge?: {
    sourceHandle?: string
    targetHandle?: string
    label?: string
    branch?: string
    itemKey?: string
  },
): FlowNode[] {
  const leaves: FlowNode[] = []
  let prev: FlowNode | undefined

  actions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const a = raw as Record<string, unknown>
    const path = `${pathPrefix}/${i}`

    if (a.choose) {
      prev = materializeChoose(ctx, a, path, { flowParent: parent, prev, firstEdge })
      leaves.push(prev)
      return
    }

    prev = expandActionItem(ctx, a, path, parent, prev, firstEdge)
    leaves.push(prev)
  })

  return leaves
}

function resolveTriggerNode(ctx: BuildContext, triggerId: string): FlowNode | undefined {
  const byHaId = ctx.nodes.find(
    n => n.kind === 'trigger' && typeof n.data.id === 'string' && n.data.id === triggerId,
  )
  if (byHaId) {
    return byHaId
  }
  const indexMatch = triggerId.match(/^trigger_(\d+)$/)
  if (indexMatch) {
    return ctx.nodes.find(n => n.path === `trigger/${indexMatch[1]}`)
  }
  return undefined
}

function connectTriggerReferenceEdges(ctx: BuildContext): void {
  const conditionNodes = ctx.nodes.filter(n => n.kind === 'condition')
  for (const cond of conditionNodes) {
    const refs = extractTriggerIdsFromCondition(cond.data)
    for (const refId of refs) {
      const trigger = resolveTriggerNode(ctx, refId)
      if (trigger) {
        connect(ctx, trigger, cond, { label: refId, edgeKind: 'reference', itemKey: refId })
      }
    }
  }

  const chooseNodes = ctx.nodes.filter(n => n.kind === 'choose')
  for (const chooseNode of chooseNodes) {
    const options = (chooseNode.data.options as Array<{ key: string; conditions: unknown[] }> | undefined) ?? []
    for (const opt of options) {
      for (const raw of opt.conditions) {
        if (!raw || typeof raw !== 'object') {
          continue
        }
        const refs = extractTriggerIdsFromCondition(raw as Record<string, unknown>)
        for (const refId of refs) {
          const trigger = resolveTriggerNode(ctx, refId)
          if (trigger) {
            connect(ctx, trigger, chooseNode, {
              label: refId,
              edgeKind: 'reference',
              targetHandle: `cond-${opt.key}`,
              itemKey: opt.key,
            })
          }
        }
      }
    }
  }
}

export function buildGraphFromConfig(
  config: Record<string, unknown>,
  options: {
    alias?: string
    mode?: string
    viewMode?: FlowViewMode
    blueprint?: {
      meta: BlueprintMeta
      inputItems: FlowListItem[]
      simulationValues: Record<string, unknown>
    }
  } = {},
): Pick<FlowDocument, 'nodes' | 'edges'> {
  const ctx: BuildContext = { nodes: [], edges: [], edgeCounter: 0 }

  if (options.blueprint) {
    const { meta, inputItems, simulationValues } = options.blueprint
    buildBlueprintGroup(ctx, meta, inputItems, simulationValues)
  }

  if (config.variables && typeof config.variables === 'object') {
    buildVariablesGroup(ctx, config.variables as Record<string, unknown>)
  }

  const triggers = (config.triggers ?? config.trigger) as unknown[] | undefined
  const triggerList = Array.isArray(triggers) ? triggers : triggers ? [triggers] : []
  const triggerNodes =
    triggerList.length > 0 ? buildTriggers(ctx, triggerList) : []
  let chainStart: FlowNode | null = triggerNodes[0] ?? null

  const conditions = (config.conditions ?? config.condition) as unknown[] | undefined
  const conditionList = Array.isArray(conditions)
    ? conditions
    : conditions
      ? [conditions]
      : []
  let afterConditions: FlowNode | null = chainStart
  if (conditionList.length > 0 && chainStart) {
    const condLeaves = buildConditions(ctx, conditionList, chainStart)
    afterConditions = condLeaves[condLeaves.length - 1] ?? chainStart
  }

  const actions = (config.actions ?? config.action ?? config.sequence) as
    | unknown[]
    | undefined
  const actionList = Array.isArray(actions) ? actions : actions ? [actions] : []
  const prefix = config.sequence ? 'sequence' : 'action'
  if (actionList.length > 0) {
    const actionAnchor = afterConditions ?? chainStart
    if (actionAnchor) {
      buildActions(ctx, actionList, actionAnchor, prefix)
    }
    else {
      buildRootActionChain(ctx, actionList, prefix)
    }
  }

  if (triggerNodes.length > 0) {
    connectTriggerReferenceEdges(ctx)
  }

  return { nodes: ctx.nodes, edges: ctx.edges }
}

const STRUCTURAL_EDGE_KINDS = new Set<FlowEdgeKind | undefined>([
  'flow',
  undefined,
])

function layoutConfigGroup(
  parent: FlowNode,
  children: FlowNode[],
  originX: number,
  layout: Record<string, { x: number; y: number }>,
): number {
  const step = FLOW_LAYOUT.configChildStep
  const header = FLOW_LAYOUT.configHeaderHeight
  const padding = FLOW_LAYOUT.configPadding
  const width = FLOW_LAYOUT.configGroupWidth
  const height = header + children.length * step + padding

  layout[parent.id] = { x: originX, y: FLOW_LAYOUT.startY }
  parent.data.groupSize = { width, height }

  children.forEach((child, i) => {
    layout[child.id] = {
      x: FLOW_LAYOUT.configPadding,
      y: header + i * step,
    }
  })

  return width
}

function layoutContainerChildren(
  container: FlowNode,
  children: FlowNode[],
  layout: Record<string, { x: number; y: number }>,
): void {
  const step = FLOW_LAYOUT.configChildStep
  const header = FLOW_LAYOUT.configHeaderHeight
  const padding = FLOW_LAYOUT.configPadding
  const width = Math.max(FLOW_LAYOUT.configGroupWidth, 200)
  const height = header + children.length * step + padding

  container.data.groupSize = { width, height }
  children.forEach((child, i) => {
    layout[child.id] = {
      x: padding,
      y: header + i * step,
    }
  })
}

export function autoLayout(
  nodes: FlowNode[],
  edges: FlowEdge[],
): Record<string, { x: number; y: number }> {
  const layout: Record<string, { x: number; y: number }> = {}
  const H_GAP = FLOW_LAYOUT.horizontalGap
  const V_GAP = FLOW_LAYOUT.verticalGap
  const execY = FLOW_LAYOUT.startY + FLOW_LAYOUT.configBandHeight

  let configX = FLOW_LAYOUT.startX
  const blueprintParent = nodes.find(n => n.kind === 'blueprint' && !n.parentId)
  if (blueprintParent) {
    const children = nodes.filter(n => n.parentId === blueprintParent.id)
    configX += layoutConfigGroup(blueprintParent, children, configX, layout) + H_GAP
  }

  const variablesParent = nodes.find(n => n.kind === 'variables' && !n.parentId)
  if (variablesParent) {
    const children = nodes.filter(
      n => n.parentId === variablesParent.id && !n.data.hidden,
    )
    layoutConfigGroup(variablesParent, children, configX, layout)
  }

  const automationRoots = nodes.filter(
    n => n.layer !== 'blueprint' && !n.parentId,
  )

  for (const container of automationRoots.filter(n => n.data.isContainer === true)) {
    const children = nodes.filter(n => n.parentId === container.id)
    layoutContainerChildren(container, children, layout)
  }

  const flowEdges = edges.filter(e => STRUCTURAL_EDGE_KINDS.has(e.edgeKind))
  const adjacency = new Map<string, string[]>()
  for (const e of flowEdges) {
    const list = adjacency.get(e.source) ?? []
    list.push(e.target)
    adjacency.set(e.source, list)
  }

  const automationNodes = automationRoots.filter(n => !n.data.isContainer || !n.parentId)
  const depth = new Map<string, number>()
  const start = automationNodes.find(n => n.kind === 'trigger') ?? automationNodes[0]

  if (start) {
    const queue: string[] = [start.id]
    depth.set(start.id, 0)
    while (queue.length > 0) {
      const id = queue.shift()!
      const d = depth.get(id) ?? 0
      for (const child of adjacency.get(id) ?? []) {
        const childNode = nodes.find(n => n.id === child)
        if (!childNode || isConfigLayerNode(childNode) || childNode.parentId) {
          continue
        }
        if (!depth.has(child)) {
          depth.set(child, d + 1)
          queue.push(child)
        }
      }
    }
  }

  for (const n of automationRoots) {
    if (!depth.has(n.id)) {
      depth.set(n.id, 0)
    }
  }

  const byDepth = new Map<number, FlowNode[]>()
  for (const n of automationRoots) {
    if (n.parentId) {
      continue
    }
    const d = depth.get(n.id) ?? 0
    const list = byDepth.get(d) ?? []
    list.push(n)
    byDepth.set(d, list)
  }

  for (const [d, group] of byDepth) {
    group.forEach((n, i) => {
      layout[n.id] = {
        x: FLOW_LAYOUT.startX + d * H_GAP,
        y: execY + i * V_GAP,
      }
    })
  }

  return layout
}
