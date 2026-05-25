import type { FlowNodeKind, FlowNodeLayer } from './types.js'

export function getNodeLayer(kind: FlowNodeKind): FlowNodeLayer {
  if (
    kind === 'blueprint'
    || kind === 'blueprint_input'
    || kind === 'variables'
  ) {
    return 'blueprint'
  }
  return 'automation'
}

export function isBlueprintLayer(kind: FlowNodeKind, layer?: FlowNodeLayer): boolean {
  return layer === 'blueprint' || getNodeLayer(kind) === 'blueprint'
}

export function isConfigLayerNode(node: { kind: FlowNodeKind; layer?: FlowNodeLayer; parentId?: string }): boolean {
  if (node.layer === 'blueprint') {
    return true
  }
  if (node.parentId && (node.kind === 'blueprint_input' || node.kind === 'variable')) {
    return true
  }
  return node.kind === 'blueprint' || node.kind === 'blueprint_input' || node.kind === 'variables'
}
