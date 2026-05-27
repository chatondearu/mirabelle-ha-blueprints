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
import {
  FLOW_LAYOUT,
  getNodeLayer,
  layoutGroupChildren,
  reconcileGroupLayouts,
} from '@mirabelle/flow-shared'
import {
  expandServiceAction,
  expandServiceActionInContainer,
  materializeChoose,
  materializeIf,
  summarizeCondition,
  summarizeHaBlock,
  summarizeServiceAction,
  type ActionBuildContext,
} from './action-expander.js'
import { layoutExecutionBand } from './execution-layout.js'
import { findBranchExitNode, resolveFlowSource } from './flow-endpoints.js'
import { getHaBlockDescriptor } from './ha-block-registry.js'
import { classifyHaItem, isHaConditionItem } from './ha-item-classifier.js'
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
    /** When false, keep source as-is (e.g. branch anchor already resolved to a child). */
    resolveSource?: boolean
  } = {},
): void {
  const edgeKind = options.edgeKind ?? 'flow'
  const isFlow = edgeKind === 'flow' || edgeKind === undefined
  const resolvedSource =
    isFlow && options.resolveSource !== false
      ? resolveFlowSource(ctx.nodes, ctx.edges, source)
      : source
  const exists = ctx.edges.some(
    e =>
      e.source === resolvedSource.id
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
    source: resolvedSource.id,
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

function asActionContext(ctx: BuildContext): ActionBuildContext {
  return {
    nodes: ctx.nodes,
    edges: ctx.edges,
    addNode: (path, kind, label, data, parentId) =>
      addNode(ctx, path, kind, label, data, parentId),
    connect: (source, target, options) => connect(ctx, source, target, options),
  }
}

function expandActionsInContainer(
  ctx: BuildContext,
  actions: unknown[],
  container: FlowNode,
  pathPrefix: string,
): FlowNode[] {
  return buildActionsInContainer(ctx, actions, container, pathPrefix)
}

const REPEAT_BODY_BRANCH = 'repeat-body'

/** Repeat body sequence is laid out outside the repeat container (like choose branches). */
function expandRepeatBlock(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
  options: {
    parentId?: string
    prev?: FlowNode
    flowParent?: FlowNode
    firstEdge?: {
      sourceHandle?: string
      targetHandle?: string
      label?: string
      branch?: string
      itemKey?: string
    }
  } = {},
): FlowNode {
  const repeatNode = addNode(
    ctx,
    path,
    'repeat',
    'Repeat',
    {
      ...a,
      blockKey: 'repeat',
      isContainer: true,
      layoutHeaderHeight: 40,
    },
    options.parentId,
  )
  if (options.prev) {
    connect(ctx, options.prev, repeatNode)
  }
  else if (options.flowParent) {
    connect(ctx, options.flowParent, repeatNode, options.firstEdge)
  }

  const repeatPayload =
    a.repeat && typeof a.repeat === 'object'
      ? (a.repeat as { sequence?: unknown[] })
      : undefined
  const body = repeatPayload?.sequence ?? []
  if (body.length > 0) {
    const leaves = buildBranchSequenceOutside(
      ctx,
      body,
      repeatNode,
      `${path}/repeat/sequence`,
      REPEAT_BODY_BRANCH,
    )
    return leaves[leaves.length - 1] ?? repeatNode
  }
  return repeatNode
}

/** Container nodes must receive the branch flow edge; expand* returns the last leaf. */
function flowEntryNodeForBranchAction(
  ctx: BuildContext,
  path: string,
  a: Record<string, unknown>,
  expanded: FlowNode,
): FlowNode {
  if (a.choose) {
    return ctx.nodes.find(n => n.path === path && n.kind === 'choose') ?? expanded
  }
  if (a.if) {
    return (
      ctx.nodes.find(
        n => n.path === path && n.kind === 'ha_block' && n.data.blockKey === 'if',
      ) ?? expanded
    )
  }
  if (a.repeat && typeof a.repeat === 'object') {
    return ctx.nodes.find(n => n.path === path && n.kind === 'repeat') ?? expanded
  }
  return expanded
}

/** Branch sequence after choose/if: nodes live outside the container parent. */
function buildBranchSequenceOutside(
  ctx: BuildContext,
  actions: unknown[],
  anchor: FlowNode,
  pathPrefix: string,
  branchKey: string,
): FlowNode[] {
  let prev: FlowNode | undefined
  const leaves: FlowNode[] = []
  actions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const a = raw as Record<string, unknown>
    const path = `${pathPrefix}/${i}`
    if (!prev) {
      const node = expandActionItemRoot(ctx, a, path)
      const flowEntry = flowEntryNodeForBranchAction(ctx, path, a, node)
      const branchSource =
        findBranchExitNode(ctx.nodes, anchor, branchKey) ?? anchor
      connect(ctx, branchSource, flowEntry, {
        itemKey: branchKey,
        branch: branchKey,
        label: branchKey,
        resolveSource: false,
      })
      prev = node
    }
    else {
      prev = expandActionItem(ctx, a, path, prev, prev)
    }
    leaves.push(prev)
  })
  return leaves
}

function summarizeAction(a: Record<string, unknown>): string {
  if (typeof a.service === 'string') {
    return summarizeServiceAction(a)
  }
  return summarizeHaBlock(a)
}

interface FlattenChainOptions {
  flowParent?: FlowNode
  container?: FlowNode
  prev?: FlowNode
  firstEdge?: {
    sourceHandle?: string
    targetHandle?: string
    label?: string
    branch?: string
    itemKey?: string
  }
}

/** Inline YAML `sequence:` lists as a linear chain (no Sequence container node). */
function buildFlattenedActionChain(
  ctx: BuildContext,
  actions: unknown[],
  pathPrefix: string,
  options: FlattenChainOptions,
): FlowNode | undefined {
  let prev = options.prev
  let last: FlowNode | undefined

  actions.forEach((raw, i) => {
    if (!raw || typeof raw !== 'object') {
      return
    }
    const a = raw as Record<string, unknown>
    const path = `${pathPrefix}/${i}`

    if (options.container) {
      last = expandActionItemInContainer(ctx, a, path, options.container, prev)
    }
    else if (!prev && options.flowParent) {
      last = expandActionItem(
        ctx,
        a,
        path,
        options.flowParent,
        undefined,
        i === 0 ? options.firstEdge : undefined,
      )
    }
    else if (!prev) {
      last = expandActionItemRoot(ctx, a, path)
    }
    else {
      last = expandActionItem(ctx, a, path, prev, prev)
    }
    prev = last
  })

  return last
}

function expandServiceAtFlowLevel(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
  parent: FlowNode,
  prev: FlowNode | undefined,
  firstEdge?: FlattenChainOptions['firstEdge'],
): FlowNode {
  const main = expandServiceAction(asActionContext(ctx), a, path)
  if (prev) {
    connect(ctx, prev, main)
  }
  else {
    connect(ctx, parent, main, firstEdge)
  }
  return main
}

function expandConditionAtFlowLevel(
  ctx: BuildContext,
  c: Record<string, unknown>,
  path: string,
  options: {
    parent?: FlowNode
    prev?: FlowNode
    firstEdge?: FlattenChainOptions['firstEdge']
    parentId?: string
    branchKey?: string
    layoutOrder?: number
  } = {},
): FlowNode {
  const node = addNode(
    ctx,
    path,
    'condition',
    summarizeCondition(c),
    {
      ...c,
      ...(options.branchKey !== undefined ? { branchKey: options.branchKey } : {}),
      ...(options.layoutOrder !== undefined ? { layoutOrder: options.layoutOrder } : {}),
    },
    options.parentId,
  )
  if (options.prev) {
    connect(ctx, options.prev, node)
  }
  else if (options.parent) {
    connect(ctx, options.parent, node, options.firstEdge)
  }
  return node
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
    const trigger = t as Record<string, unknown>
    if (classifyHaItem(trigger) !== 'trigger') {
      return
    }
    const path = `trigger/${i}`
    const node = addNode(
      ctx,
      path,
      'trigger',
      summarizeTrigger(trigger),
      trigger,
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
    const cond = c as Record<string, unknown>
    if (!isHaConditionItem(cond)) {
      return
    }
    const path = `condition/${i}`
    const node = addNode(
      ctx,
      path,
      'condition',
      summarizeCondition(cond),
      cond,
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
  if (classifyHaItem(a) === 'condition') {
    return expandConditionAtFlowLevel(ctx, a, path, { parent, prev, firstEdge })
  }

  if (Array.isArray(a.sequence)) {
    if (prev) {
      return (
        buildFlattenedActionChain(ctx, a.sequence, `${path}/sequence`, { prev })
        ?? prev
      )
    }
    return (
      buildFlattenedActionChain(ctx, a.sequence, `${path}/sequence`, {
        flowParent: parent,
        firstEdge,
      }) ?? parent
    )
  }

  if (a.repeat && typeof a.repeat === 'object') {
    return expandRepeatBlock(ctx, a, path, { prev, flowParent: parent, firstEdge })
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

  if (a.if) {
    return materializeIf(
      asActionContext(ctx),
      a,
      path,
      { flowParent: parent, prev, firstEdge },
      (actx, actions, anchor, prefix, branchKey) =>
        buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
    )
  }

  if (typeof a.service === 'string') {
    return expandServiceAtFlowLevel(ctx, a, path, parent, prev, firstEdge)
  }

  const descriptor = getHaBlockDescriptor(a)
  const node = addNode(ctx, path, descriptor.nodeKind, summarizeAction(a), a, undefined)
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
  if (classifyHaItem(a) === 'condition') {
    return expandConditionAtFlowLevel(ctx, a, path)
  }

  if (a.choose) {
    return materializeChoose(
      asActionContext(ctx),
      a,
      path,
      {},
      (actx, actions, anchor, prefix, branchKey) =>
        buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
    )
  }

  if (a.if) {
    return materializeIf(
      asActionContext(ctx),
      a,
      path,
      {},
      (actx, actions, anchor, prefix, branchKey) =>
        buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
    )
  }

  if (a.repeat && typeof a.repeat === 'object') {
    return expandRepeatBlock(ctx, a, path)
  }

  if (typeof a.service === 'string') {
    return expandServiceAction(asActionContext(ctx), a, path)
  }

  if (Array.isArray(a.sequence)) {
    const last = buildFlattenedActionChain(ctx, a.sequence, `${path}/sequence`, {})
    if (last) {
      return last
    }
    return addNode(
      ctx,
      `${path}/sequence`,
      'ha_block',
      'Empty sequence',
      { blockKey: 'sequence', empty: true },
      undefined,
    )
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

function expandActionItemInContainer(
  ctx: BuildContext,
  a: Record<string, unknown>,
  path: string,
  container: FlowNode,
  prev: FlowNode | undefined,
): FlowNode {
  if (classifyHaItem(a) === 'condition') {
    return expandConditionAtFlowLevel(ctx, a, path, {
      parentId: container.id,
      prev,
    })
  }

  if (a.choose) {
    return materializeChoose(
      asActionContext(ctx),
      a,
      path,
      { parentId: container.id, prev },
      (actx, actions, anchor, prefix, branchKey) =>
        buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
    )
  }

  if (a.if) {
    return materializeIf(
      asActionContext(ctx),
      a,
      path,
      { parentId: container.id, prev },
      (actx, actions, anchor, prefix, branchKey) =>
        buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
    )
  }

  if (a.repeat && typeof a.repeat === 'object') {
    return expandRepeatBlock(ctx, a, path, { parentId: container.id, prev })
  }

  if (typeof a.service === 'string') {
    return expandServiceActionInContainer(
      asActionContext(ctx),
      a,
      path,
      container,
      prev,
    )
  }

  if (Array.isArray(a.sequence)) {
    if (prev) {
      return (
        buildFlattenedActionChain(ctx, a.sequence, `${path}/sequence`, {
          container,
          prev,
        }) ?? prev
      )
    }
    return (
      buildFlattenedActionChain(ctx, a.sequence, `${path}/sequence`, {
        container,
      }) ?? container
    )
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
      prev = materializeChoose(
        asActionContext(ctx),
        a,
        path,
        { flowParent: parent, prev, firstEdge },
        (actx, actions, anchor, prefix, branchKey) =>
          buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
      )
      leaves.push(prev)
      return
    }

    if (a.if) {
      prev = materializeIf(
        asActionContext(ctx),
        a,
        path,
        { flowParent: parent, prev, firstEdge },
        (actx, actions, anchor, prefix, branchKey) =>
          buildBranchSequenceOutside(ctx, actions, anchor, prefix, branchKey),
      )
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
}

function triggerMatchesConditionRef(trigger: FlowNode, refId: string): boolean {
  const haId = typeof trigger.data.id === 'string' ? trigger.data.id : undefined
  if (haId && haId === refId) {
    return true
  }
  const indexMatch = refId.match(/^trigger_(\d+)$/)
  return indexMatch !== null && trigger.path === `trigger/${indexMatch[1]}`
}

function findExplicitTriggerFlowTargets(
  ctx: BuildContext,
  trigger: FlowNode,
): FlowNode[] {
  return ctx.nodes.filter(
    n =>
      n.kind === 'condition'
      && extractTriggerIdsFromCondition(n.data).some(refId =>
        triggerMatchesConditionRef(trigger, refId),
      ),
  )
}

/** First executable node after triggers (global condition or first action anchor). */
function findDefaultExecutionEntry(ctx: BuildContext): FlowNode | undefined {
  const rootCondition = ctx.nodes.find(n => n.path === 'condition/0')
  if (rootCondition) {
    return rootCondition
  }

  const firstTrigger = ctx.nodes.find(n => n.path === 'trigger/0')
  if (firstTrigger) {
    const anchorEdge = ctx.edges.find(
      e =>
        e.source === firstTrigger.id
        && (e.edgeKind === 'flow' || e.edgeKind === undefined),
    )
    if (anchorEdge) {
      return ctx.nodes.find(n => n.id === anchorEdge.target)
    }
  }

  return ctx.nodes.find(
    n =>
      n.path === 'action/0'
      || (n.path?.startsWith('action/0/') && !n.path.includes('/choose/')),
  )
}

function hasFlowEdgeTo(ctx: BuildContext, sourceId: string, targetId: string): boolean {
  return ctx.edges.some(
    e =>
      e.source === sourceId
      && e.target === targetId
      && (e.edgeKind === 'flow' || e.edgeKind === undefined),
  )
}

/** Wire every root trigger into the execution graph (not only trigger/0). */
function connectTriggerFlowEdges(ctx: BuildContext): void {
  const rootTriggers = ctx.nodes.filter(
    n => n.kind === 'trigger' && !n.parentId,
  )
  if (rootTriggers.length === 0) {
    return
  }

  const defaultEntry = findDefaultExecutionEntry(ctx)

  for (const trigger of rootTriggers) {
    const explicitTargets = findExplicitTriggerFlowTargets(ctx, trigger)
    const targets =
      explicitTargets.length > 0
        ? explicitTargets
        : defaultEntry
          ? [defaultEntry]
          : []

    for (const target of targets) {
      if (!hasFlowEdgeTo(ctx, trigger.id, target.id)) {
        connect(ctx, trigger, target)
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
    connectTriggerFlowEdges(ctx)
  }

  return { nodes: ctx.nodes, edges: ctx.edges }
}

function layoutConfigGroup(
  parent: FlowNode,
  children: FlowNode[],
  originX: number,
  layout: Record<string, { x: number; y: number }>,
): number {
  const { positions, size } = layoutGroupChildren(children, {
    minWidth: FLOW_LAYOUT.configGroupWidth,
  })

  layout[parent.id] = { x: originX, y: FLOW_LAYOUT.startY }
  parent.data.groupSize = size
  for (const [childId, pos] of Object.entries(positions)) {
    layout[childId] = pos
  }

  return size.width
}

export function autoLayout(
  nodes: FlowNode[],
  edges: FlowEdge[],
): Record<string, { x: number; y: number }> {
  const layout: Record<string, { x: number; y: number }> = {}
  const H_GAP = FLOW_LAYOUT.horizontalGap

  let configX = FLOW_LAYOUT.startX
  let configBandBottom = FLOW_LAYOUT.startY + FLOW_LAYOUT.configBandMinHeight
  const blueprintParent = nodes.find(n => n.kind === 'blueprint' && !n.parentId)
  if (blueprintParent) {
    const children = nodes.filter(n => n.parentId === blueprintParent.id)
    configX += layoutConfigGroup(blueprintParent, children, configX, layout) + H_GAP
    const size = blueprintParent.data.groupSize as { height: number } | undefined
    if (size) {
      configBandBottom = Math.max(
        configBandBottom,
        FLOW_LAYOUT.startY + size.height,
      )
    }
  }

  const variablesParent = nodes.find(n => n.kind === 'variables' && !n.parentId)
  if (variablesParent) {
    const children = nodes.filter(
      n => n.parentId === variablesParent.id && !n.data.hidden,
    )
    layoutConfigGroup(variablesParent, children, configX, layout)
    const size = variablesParent.data.groupSize as { height: number } | undefined
    if (size) {
      configBandBottom = Math.max(
        configBandBottom,
        FLOW_LAYOUT.startY + size.height,
      )
    }
  }

  reconcileGroupLayouts(nodes, layout, n => n.data.hidden !== true)

  const execY = configBandBottom + FLOW_LAYOUT.configExecGap
  const execLayout = layoutExecutionBand(nodes, edges, execY)
  Object.assign(layout, execLayout)

  return layout
}
