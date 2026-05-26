import type { FlowEdge, FlowEdgeKind, FlowNodeKind } from '@mirabelle/flow-shared'

const BINDING_IN_KINDS = new Set<FlowEdgeKind>([
  'input_binding',
  'variable_binding',
  'reference',
])

export interface NodeHandleVisibility {
  showTarget: boolean
  showSource: boolean
}

function isFlowEdge(edgeKind: FlowEdgeKind | undefined): boolean {
  return edgeKind === 'flow' || edgeKind === undefined
}

function isBindingInEdge(edgeKind: FlowEdgeKind | undefined): boolean {
  return edgeKind !== undefined && BINDING_IN_KINDS.has(edgeKind)
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

  const flowInFromOutside = incoming.some((e) => {
    if (!isFlowEdge(e.edgeKind)) {
      return false
    }
    if (!childIds) {
      return true
    }
    return !childIds.has(e.source)
  })

  const bindingIn = incoming.some(e => isBindingInEdge(e.edgeKind))
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
      showSource: false,
    }
  }

  if (isChild) {
    return {
      showTarget: bindingIn,
      showSource: isBindingSource ? bindingOut : flowOut,
    }
  }

  return {
    showTarget: bindingIn || flowIn,
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
