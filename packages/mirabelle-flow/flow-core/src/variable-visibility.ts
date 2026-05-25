import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { isConfigLayerNode } from '@mirabelle/flow-shared'

function isAutomationConsumer(node: FlowNode): boolean {
  if (isConfigLayerNode(node)) {
    return false
  }
  if (node.kind === 'variable') {
    return false
  }
  return true
}

/**
 * Hide variable child nodes with no variable_binding to an automation consumer (binding_only rule).
 */
export function applyVariableVisibility(nodes: FlowNode[], edges: FlowEdge[]): void {
  const variableNodes = nodes.filter(n => n.kind === 'variable')
  if (variableNodes.length === 0) {
    return
  }

  const externalConsumers = new Set(
    nodes.filter(isAutomationConsumer).map(n => n.id),
  )

  for (const variable of variableNodes) {
    const hasExternalBinding = edges.some(
      e =>
        e.edgeKind === 'variable_binding'
        && e.source === variable.id
        && externalConsumers.has(e.target),
    )
    variable.data.hidden = !hasExternalBinding
  }
}
