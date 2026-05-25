import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'

function isFlowEdge(edgeKind: FlowEdge['edgeKind'] | undefined): boolean {
  return edgeKind === undefined || edgeKind === 'flow'
}

/** Last condition or branch marker child used as the flow source for a choose/if branch. */
export function findBranchExitNode(
  nodes: FlowNode[],
  container: FlowNode,
  branchKey: string,
): FlowNode | undefined {
  const children = nodes.filter(n => n.parentId === container.id)
  const marker = children.find(
    n => n.kind === 'choose_option' && n.data.key === branchKey,
  )
  if (marker) {
    return marker
  }

  const conditions = children.filter(
    n => n.kind === 'condition' && n.data.branchKey === branchKey,
  )
  if (conditions.length === 0) {
    return undefined
  }

  return conditions.sort(
    (a, b) =>
      (Number(b.data.layoutOrder) || 0) - (Number(a.data.layoutOrder) || 0),
  )[0]
}

/** Deepest visible child that should emit structural flow edges for a container. */
export function findContainerFlowExit(
  nodes: FlowNode[],
  edges: FlowEdge[],
  container: FlowNode,
): FlowNode | undefined {
  if (container.data.isContainer !== true && container.kind !== 'sequence') {
    return undefined
  }

  const children = nodes.filter(n => n.parentId === container.id)
  if (children.length === 0) {
    return undefined
  }

  const childIds = new Set(children.map(c => c.id))
  const internalFlow = edges.filter(
    e => isFlowEdge(e.edgeKind) && childIds.has(e.source) && childIds.has(e.target),
  )
  const hasOutgoing = new Set(internalFlow.map(e => e.source))
  const sinks = children.filter(c => !hasOutgoing.has(c.id))
  const candidates = sinks.length > 0 ? sinks : children

  const leaf = [...candidates].sort(
    (a, b) =>
      (Number(b.data.layoutOrder) || 0) - (Number(a.data.layoutOrder) || 0),
  )[0]
  if (!leaf) {
    return undefined
  }

  if (leaf.data.isContainer === true) {
    return findContainerFlowExit(nodes, edges, leaf) ?? leaf
  }

  const nested = nodes.filter(n => n.parentId === leaf.id)
  if (nested.length > 0) {
    return nested.sort(
      (a, b) =>
        (Number(b.data.layoutOrder) || 0) - (Number(a.data.layoutOrder) || 0),
    )[0] ?? leaf
  }

  return leaf
}

export function resolveFlowSource(
  nodes: FlowNode[],
  edges: FlowEdge[],
  node: FlowNode,
): FlowNode {
  return findContainerFlowExit(nodes, edges, node) ?? node
}
