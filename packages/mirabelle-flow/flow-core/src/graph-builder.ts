import type { FlowDocument, FlowEdge, FlowNode, FlowNodeKind } from '@mirabelle/flow-shared'

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
  const id = path.replace(/\//g, '_') || 'root'
  const node: FlowNode = { id, kind, label, path, data, parentId }
  ctx.nodes.push(node)
  return node
}

function connect(
  ctx: BuildContext,
  source: FlowNode,
  target: FlowNode,
  label?: string,
  branch?: string,
): void {
  ctx.edges.push({
    id: nextEdgeId(ctx),
    source: source.id,
    target: target.id,
    label,
    branch,
  })
}

function summarizeTrigger(t: Record<string, unknown>): string {
  const platform = (t.platform ?? t.trigger) as string | undefined
  const entity = t.entity_id as string | undefined
  if (platform && entity) {
    return `Trigger: ${platform} (${entity})`
  }
  if (platform) {
    return `Trigger: ${platform}`
  }
  return 'Trigger'
}

function summarizeCondition(c: Record<string, unknown>): string {
  const cond = c.condition as string | undefined
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
  return 'Action'
}

function buildTriggers(
  ctx: BuildContext,
  triggers: unknown[],
  parent: FlowNode,
): FlowNode[] {
  const leaves: FlowNode[] = []
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
      parent.id,
    )
    connect(ctx, parent, node)
    leaves.push(node)
  })
  return leaves
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
      parent.id,
    )
    connect(ctx, parent, node)
    leaves.push(node)
  })
  return leaves
}

function buildActions(
  ctx: BuildContext,
  actions: unknown[],
  parent: FlowNode,
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

    if (a.choose) {
      const chooseNode = addNode(ctx, path, 'choose', 'Choose', { choose: a.choose }, parent.id)
      if (prev) {
        connect(ctx, prev, chooseNode)
      }
      else {
        connect(ctx, parent, chooseNode)
      }

      const choose = a.choose as Array<{
        conditions?: unknown[]
        sequence?: unknown[]
      }>
      const branchLeaves: FlowNode[] = []

      choose.forEach((branch, bi) => {
        const branchPath = `${path}/choose/${bi}`
        const conds = branch.conditions ?? []
        const seq = branch.sequence ?? []
        let branchParent = chooseNode

        if (conds.length > 0) {
          const condNode = addNode(
            ctx,
            `${branchPath}/conditions`,
            'condition',
            `Branch ${bi + 1} conditions`,
            { conditions: conds },
            chooseNode.id,
          )
          connect(ctx, chooseNode, condNode, `Branch ${bi + 1}`, String(bi))
          branchParent = condNode
        }

        const seqLeaves = buildActions(ctx, seq, branchParent, `${branchPath}/sequence`)
        branchLeaves.push(...(seqLeaves.length ? seqLeaves : [branchParent]))
      })

      const defaultSeq = (a as { default?: unknown[] }).default ?? []
      if (defaultSeq.length > 0) {
        const defLeaves = buildActions(ctx, defaultSeq, chooseNode, `${path}/default`)
        branchLeaves.push(...defLeaves)
      }

      prev = branchLeaves[branchLeaves.length - 1] ?? chooseNode
      leaves.push(prev)
      return
    }

    const node = addNode(
      ctx,
      path,
      'action',
      summarizeAction(a),
      a,
      parent.id,
    )
    if (prev) {
      connect(ctx, prev, node)
    }
    else {
      connect(ctx, parent, node)
    }
    prev = node
    leaves.push(node)
  })

  return leaves
}

function buildVariables(
  ctx: BuildContext,
  variables: Record<string, unknown>,
  parent: FlowNode,
): FlowNode {
  const node = addNode(ctx, 'variables', 'variables', 'Variables', variables, parent.id)
  connect(ctx, parent, node)
  return node
}

export function buildGraphFromConfig(
  config: Record<string, unknown>,
  options: { alias?: string; mode?: string } = {},
): Pick<FlowDocument, 'nodes' | 'edges'> {
  const ctx: BuildContext = { nodes: [], edges: [], edgeCounter: 0 }

  const root = addNode(ctx, 'root', 'root', options.alias ?? 'Automation', {}, undefined)

  if (config.variables && typeof config.variables === 'object') {
    buildVariables(ctx, config.variables as Record<string, unknown>, root)
  }

  const triggers = (config.triggers ?? config.trigger) as unknown[] | undefined
  let chainStart = root
  const triggerList = Array.isArray(triggers) ? triggers : triggers ? [triggers] : []
  if (triggerList.length > 0) {
    const triggerLeaves = buildTriggers(ctx, triggerList, root)
    chainStart = triggerLeaves[0] ?? root
  }

  const conditions = (config.conditions ?? config.condition) as unknown[] | undefined
  const conditionList = Array.isArray(conditions)
    ? conditions
    : conditions
      ? [conditions]
      : []
  let afterConditions = chainStart
  if (conditionList.length > 0) {
    const condLeaves = buildConditions(ctx, conditionList, chainStart)
    afterConditions = condLeaves[condLeaves.length - 1] ?? chainStart
  }

  const actions = (config.actions ?? config.action ?? config.sequence) as
    | unknown[]
    | undefined
  const actionList = Array.isArray(actions) ? actions : actions ? [actions] : []
  const prefix = config.sequence ? 'sequence' : 'action'
  if (actionList.length > 0) {
    buildActions(ctx, actionList, afterConditions, prefix)
  }

  return { nodes: ctx.nodes, edges: ctx.edges }
}

export function autoLayout(
  nodes: FlowNode[],
  edges: FlowEdge[],
): Record<string, { x: number; y: number }> {
  const layout: Record<string, { x: number; y: number }> = {}
  const H_GAP = 280
  const V_GAP = 100

  const adjacency = new Map<string, string[]>()
  for (const e of edges) {
    const list = adjacency.get(e.source) ?? []
    list.push(e.target)
    adjacency.set(e.source, list)
  }

  const depth = new Map<string, number>()
  const root = nodes.find(n => n.kind === 'root')
  if (!root) {
    nodes.forEach((n, i) => {
      layout[n.id] = { x: 80, y: 80 + i * V_GAP }
    })
    return layout
  }

  const queue: string[] = [root.id]
  depth.set(root.id, 0)
  while (queue.length > 0) {
    const id = queue.shift()!
    const d = depth.get(id) ?? 0
    for (const child of adjacency.get(id) ?? []) {
      if (!depth.has(child)) {
        depth.set(child, d + 1)
        queue.push(child)
      }
    }
  }

  const byDepth = new Map<number, FlowNode[]>()
  for (const n of nodes) {
    const d = depth.get(n.id) ?? 0
    const list = byDepth.get(d) ?? []
    list.push(n)
    byDepth.set(d, list)
  }

  for (const [d, group] of byDepth) {
    group.forEach((n, i) => {
      layout[n.id] = { x: 80 + d * H_GAP, y: 80 + i * V_GAP }
    })
  }

  return layout
}
