import type { FlowEdge, FlowEdgeKind, FlowNodeKind } from '@mirabelle/flow-shared'

/** Target handle for dashed semantic edges (reference, bindings). */
export const TARGET_TOP_HANDLE_ID = 'target-top'

export interface NodeHandleVisibility {
  /** Left target for solid execution (`flow`) edges. */
  showTarget: boolean
  /** Top target for dashed semantic edges (reference, input/variable bindings). */
  showTargetTop: boolean
  showSource: boolean
}

function isFlowEdge(edgeKind: FlowEdgeKind | undefined): boolean {
  return edgeKind === 'flow' || edgeKind === undefined
}

function isDashedTargetEdge(edgeKind: FlowEdgeKind | undefined): boolean {
  return (
    edgeKind === 'reference'
    || edgeKind === 'input_binding'
    || edgeKind === 'variable_binding'
  )
}

export function edgeUsesTopTarget(edgeKind: FlowEdgeKind | undefined): boolean {
  return isDashedTargetEdge(edgeKind)
}

export function computeNodeHandleVisibility(
  nodeId: string,
  kind: FlowNodeKind,
  parentId: string | undefined,
  isContainer: boolean,
  edges: FlowEdge[],
  childIdsByParent: ReadonlyMap<string, ReadonlySet<string>>,
): NodeHandleVisibility {
  const incoming = edges.filter(e => e.target === nodeId)
  const outgoing = edges.filter(e => e.source === nodeId)
  const childIds = childIdsByParent.get(nodeId)

  if (kind === 'trigger') {
    return {
      showTarget: incoming.some(e => isFlowEdge(e.edgeKind)),
      showTargetTop: incoming.some(e => isDashedTargetEdge(e.edgeKind)),
      showSource: true,
    }
  }

  const flowInFromOutside = incoming.some((e) => {
    if (!isFlowEdge(e.edgeKind)) {
      return false
    }
    if (!childIds) {
      return true
    }
    return !childIds.has(e.source)
  })

  const dashedIn = incoming.some(e => isDashedTargetEdge(e.edgeKind))
  const flowIn = incoming.some(e => isFlowEdge(e.edgeKind))
  const flowOut = outgoing.some(e => isFlowEdge(e.edgeKind))
  const bindingOut = outgoing.some(
    e => e.edgeKind === 'input_binding' || e.edgeKind === 'variable_binding',
  )
  const isChild = Boolean(parentId)
  const isBindingSource = kind === 'blueprint_input' || kind === 'variable'
  const isGroupParent =
    isContainer || kind === 'blueprint' || kind === 'variables'

  if (isGroupParent) {
    return {
      showTarget: flowInFromOutside,
      showTargetTop: dashedIn,
      showSource: false,
    }
  }

  if (isChild) {
    return {
      showTarget: flowIn,
      showTargetTop: dashedIn,
      showSource: isBindingSource ? bindingOut : flowOut,
    }
  }

  return {
    showTarget: flowIn,
    showTargetTop: dashedIn,
    showSource: isBindingSource ? bindingOut : flowOut,
  }
}

export function buildChildIdsByParent(
  nodes: Array<{ id: string, parentId?: string }>,
): Map<string, Set<string>> {
  const map = new Map<string, Set<string>>()
  for (const node of nodes) {
    if (!node.parentId) {
      continue
    }
    const set = map.get(node.parentId) ?? new Set()
    set.add(node.id)
    map.set(node.parentId, set)
  }
  return map
}
