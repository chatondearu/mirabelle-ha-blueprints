import type { FlowNodeKind, FlowNodeLayer } from './types.js'

export function getNodeLayer(kind: FlowNodeKind): FlowNodeLayer {
  if (
    kind === 'blueprint_meta'
    || kind === 'blueprint_input'
    || kind === 'inputs'
    || kind === 'inputs_variables'
    || kind === 'variables'
  ) {
    return 'blueprint'
  }
  return 'automation'
}

export function isBlueprintLayer(kind: FlowNodeKind, layer?: FlowNodeLayer): boolean {
  return layer === 'blueprint' || getNodeLayer(kind) === 'blueprint'
}
