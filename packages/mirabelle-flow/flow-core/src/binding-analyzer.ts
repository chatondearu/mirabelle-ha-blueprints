import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { inputRefKey } from './yaml.js'

let bindingEdgeCounter = 0

function nextBindingId(): string {
  bindingEdgeCounter += 1
  return `e-binding-${bindingEdgeCounter}`
}

export function resetBindingEdgeCounter(): void {
  bindingEdgeCounter = 0
}

function walkForInputRefs(
  value: unknown,
  consumerId: string,
  sourceNodeId: string,
  inputSourceHandles: Map<string, string>,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  const key = inputRefKey(value)
  if (key) {
    const edgeKey = `${sourceNodeId}|input|${key}|${consumerId}`
    if (!seen.has(edgeKey)) {
      seen.add(edgeKey)
      edges.push({
        id: nextBindingId(),
        source: sourceNodeId,
        sourceHandle: inputSourceHandles.get(key),
        target: consumerId,
        label: key,
        edgeKind: 'input_binding',
        itemKey: key,
      })
    }
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      walkForInputRefs(item, consumerId, sourceNodeId, inputSourceHandles, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForInputRefs(v, consumerId, sourceNodeId, inputSourceHandles, edges, seen)
    }
  }
}

const VARIABLE_PATTERNS = [
  /\bvariables\.([a-zA-Z_][\w]*)/g,
  /\{\{\s*([a-zA-Z_][\w]*)\s*[\.\|\}]/g,
  /\{\{\s*([a-zA-Z_][\w]*)\s*\}\}/g,
]

function extractVariableNamesFromText(text: string): string[] {
  const names = new Set<string>()
  for (const pattern of VARIABLE_PATTERNS) {
    pattern.lastIndex = 0
    let match = pattern.exec(text)
    while (match) {
      const name = match[1]
      if (name && name !== 'trigger' && name !== 'states') {
        names.add(name)
      }
      match = pattern.exec(text)
    }
  }
  return [...names]
}

export function analyzeBindings(nodes: FlowNode[]): FlowEdge[] {
  resetBindingEdgeCounter()
  const edges: FlowEdge[] = []
  const seen = new Set<string>()
  const inputSourceNode =
    nodes.find(n => n.kind === 'inputs' || n.kind === 'inputs_variables')
    ?? nodes.find(n => n.kind === 'blueprint_meta')
  const inputSourceId = inputSourceNode?.id ?? 'blueprint_meta'
  const inputSourceHandles = new Map<string, string>()
  if (inputSourceNode && Array.isArray(inputSourceNode.data.items)) {
    for (const item of inputSourceNode.data.items as Array<{ key: string }>) {
      inputSourceHandles.set(item.key, `inp-${item.key}`)
    }
  }
  const variableSourceNode =
    nodes.find(n => n.kind === 'variables' || n.kind === 'inputs_variables')

  const variableItems = new Map<string, { sourceId: string; sourceHandle?: string }>()
  if (variableSourceNode && Array.isArray(variableSourceNode.data.items)) {
    for (const item of variableSourceNode.data.items as Array<{ key: string }>) {
      variableItems.set(item.key, {
        sourceId: variableSourceNode.id,
        sourceHandle: `var-${item.key}`,
      })
    }
  }

  for (const node of nodes) {
    if (
      node.kind === 'blueprint_meta'
      || node.kind === 'inputs'
      || node.kind === 'variables'
      || node.kind === 'inputs_variables'
    ) {
      continue
    }
    walkForInputRefs(
      node.data,
      node.id,
      inputSourceId,
      inputSourceHandles,
      edges,
      seen,
    )
    if (typeof node.data === 'object') {
      walkForVariableRefsWithItems(node.data, node.id, variableItems, edges, seen)
    }
  }

  return edges
}

function walkForVariableRefsWithItems(
  value: unknown,
  consumerId: string,
  variableItems: Map<string, { sourceId: string; sourceHandle?: string }>,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  if (typeof value === 'string') {
    const names = new Set<string>(extractVariableNamesFromText(value))
    for (const key of variableItems.keys()) {
      const pattern = new RegExp(`\\b${key}\\b`)
      if (pattern.test(value)) {
        names.add(key)
      }
    }
    for (const name of names) {
      const source = variableItems.get(name)
      if (!source) {
        continue
      }
      const edgeKey = `${source.sourceId}|var|${name}|${consumerId}`
      if (!seen.has(edgeKey)) {
        seen.add(edgeKey)
        edges.push({
          id: nextBindingId(),
          source: source.sourceId,
          sourceHandle: source.sourceHandle,
          target: consumerId,
          label: name,
          edgeKind: 'variable_binding',
          itemKey: name,
        })
      }
    }
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      walkForVariableRefsWithItems(item, consumerId, variableItems, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForVariableRefsWithItems(v, consumerId, variableItems, edges, seen)
    }
  }
}

/** Nodes and edges reachable from a binding source (meta input key or variable name). */
export function getBindingHighlight(
  sourceNodeId: string,
  bindingLabel: string | undefined,
  nodes: FlowNode[],
  edges: FlowEdge[],
): { nodeIds: Set<string>, edgeIds: Set<string> } {
  const nodeIds = new Set<string>([sourceNodeId])
  const edgeIds = new Set<string>()

  for (const edge of edges) {
    if (edge.source !== sourceNodeId) {
      continue
    }
    if (bindingLabel !== undefined && edge.label !== bindingLabel) {
      continue
    }
    if (edge.edgeKind === 'input_binding' || edge.edgeKind === 'variable_binding') {
      nodeIds.add(edge.target)
      edgeIds.add(edge.id)
    }
  }

  return { nodeIds, edgeIds }
}
