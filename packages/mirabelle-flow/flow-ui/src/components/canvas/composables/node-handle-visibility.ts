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

export function computeNodeHandleVisibility(
  nodeId: string,
  kind: FlowNodeKind,
  parentId: string | undefined,
  isContainer: boolean,
  edges: FlowEdge[],
): NodeHandleVisibility {
  if (
    isContainer
    || kind === 'blueprint'
    || kind === 'variables'
  ) {
    return { showTarget: false, showSource: false }
  }

  const incoming = edges.filter(e => e.target === nodeId)
  const outgoing = edges.filter(e => e.source === nodeId)
  const bindingIn = incoming.some(
    e => e.edgeKind !== undefined && BINDING_IN_KINDS.has(e.edgeKind),
  )
  const flowIn = incoming.some(e => e.edgeKind === 'flow' || e.edgeKind === undefined)
  const flowOut = outgoing.some(e => e.edgeKind === 'flow' || e.edgeKind === undefined)
  const bindingOut = outgoing.some(
    e => e.edgeKind === 'input_binding' || e.edgeKind === 'variable_binding',
  )
  const isChild = Boolean(parentId)
  const isBindingSource = kind === 'blueprint_input' || kind === 'variable'

  return {
    showTarget: isChild ? bindingIn : bindingIn || flowIn,
    showSource: isBindingSource ? bindingOut : flowOut,
  }
}
