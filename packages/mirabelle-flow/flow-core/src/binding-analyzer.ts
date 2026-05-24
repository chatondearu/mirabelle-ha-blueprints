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
  metaId: string,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  const key = inputRefKey(value)
  if (key) {
    const edgeKey = `${metaId}|input|${key}|${consumerId}`
    if (!seen.has(edgeKey)) {
      seen.add(edgeKey)
      edges.push({
        id: nextBindingId(),
        source: metaId,
        target: consumerId,
        label: key,
        edgeKind: 'input_binding',
      })
    }
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      walkForInputRefs(item, consumerId, metaId, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForInputRefs(v, consumerId, metaId, edges, seen)
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

function walkForVariableRefs(
  value: unknown,
  consumerId: string,
  variableIds: Map<string, string>,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  if (typeof value === 'string') {
    for (const name of extractVariableNamesFromText(value)) {
      const varNodeId = variableIds.get(name)
      if (!varNodeId) {
        continue
      }
      const edgeKey = `${varNodeId}|var|${consumerId}`
      if (!seen.has(edgeKey)) {
        seen.add(edgeKey)
        edges.push({
          id: nextBindingId(),
          source: varNodeId,
          target: consumerId,
          label: name,
          edgeKind: 'variable_binding',
        })
      }
    }
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      walkForVariableRefs(item, consumerId, variableIds, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForVariableRefs(v, consumerId, variableIds, edges, seen)
    }
  }
}

export function analyzeBindings(nodes: FlowNode[]): FlowEdge[] {
  resetBindingEdgeCounter()
  const edges: FlowEdge[] = []
  const seen = new Set<string>()
  const meta = nodes.find(n => n.kind === 'blueprint_meta')
  const metaId = meta?.id ?? 'blueprint_meta'

  const variableIds = new Map<string, string>()
  for (const node of nodes) {
    if (node.kind === 'variable') {
      const name = node.path.replace(/^variables\//, '')
      variableIds.set(name, node.id)
    }
  }

  for (const node of nodes) {
    if (node.kind === 'blueprint_meta') {
      continue
    }
    walkForInputRefs(node.data, node.id, metaId, edges, seen)
    walkForVariableRefs(node.data, node.id, variableIds, edges, seen)
  }

  return edges
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
