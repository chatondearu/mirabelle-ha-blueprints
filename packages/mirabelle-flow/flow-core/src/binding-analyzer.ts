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
  inputNodesByKey: Map<string, string>,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  const key = inputRefKey(value)
  if (key) {
    const sourceId = inputNodesByKey.get(key)
    if (!sourceId) {
      return
    }
    const edgeKey = `${sourceId}|input|${key}|${consumerId}`
    if (!seen.has(edgeKey)) {
      seen.add(edgeKey)
      edges.push({
        id: nextBindingId(),
        source: sourceId,
        sourceHandle: `inp-${key}`,
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
      walkForInputRefs(item, consumerId, inputNodesByKey, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForInputRefs(v, consumerId, inputNodesByKey, edges, seen)
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

const SKIP_BINDING_WALK_KINDS = new Set([
  'blueprint',
  'blueprint_input',
  'variables',
  'variable',
])

export function analyzeBindings(nodes: FlowNode[]): FlowEdge[] {
  resetBindingEdgeCounter()
  const edges: FlowEdge[] = []
  const seen = new Set<string>()

  const inputNodesByKey = new Map<string, string>()
  for (const node of nodes.filter(n => n.kind === 'blueprint_input')) {
    const key = (node.data.key ?? node.path.replace(/^.*\//, '')) as string
    inputNodesByKey.set(key, node.id)
  }

  const variableNodesByName = new Map<string, string>()
  for (const node of nodes.filter(n => n.kind === 'variable')) {
    const name = (node.data.name ?? node.label) as string
    variableNodesByName.set(name, node.id)
  }

  for (const node of nodes) {
    if (SKIP_BINDING_WALK_KINDS.has(node.kind)) {
      continue
    }
    walkForInputRefs(node.data, node.id, inputNodesByKey, edges, seen)
    walkForVariableRefsWithItems(node.data, node.id, variableNodesByName, edges, seen)
  }

  return edges
}

function walkForVariableRefsWithItems(
  value: unknown,
  consumerId: string,
  variableNodesByName: Map<string, string>,
  edges: FlowEdge[],
  seen: Set<string>,
): void {
  if (typeof value === 'string') {
    const names = new Set<string>(extractVariableNamesFromText(value))
    for (const key of variableNodesByName.keys()) {
      const pattern = new RegExp(`\\b${key}\\b`)
      if (pattern.test(value)) {
        names.add(key)
      }
    }
    for (const name of names) {
      const sourceId = variableNodesByName.get(name)
      if (!sourceId) {
        continue
      }
      const edgeKey = `${sourceId}|var|${name}|${consumerId}`
      if (!seen.has(edgeKey)) {
        seen.add(edgeKey)
        edges.push({
          id: nextBindingId(),
          source: sourceId,
          sourceHandle: `var-${name}`,
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
      walkForVariableRefsWithItems(item, consumerId, variableNodesByName, edges, seen)
    }
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      walkForVariableRefsWithItems(v, consumerId, variableNodesByName, edges, seen)
    }
  }
}

/** Nodes and edges reachable from a binding source (input or variable child node). */
export function getBindingHighlight(
  sourceNodeId: string,
  bindingLabel: string | undefined,
  nodes: FlowNode[],
  edges: FlowEdge[],
): { nodeIds: Set<string>, edgeIds: Set<string> } {
  const nodeIds = new Set<string>([sourceNodeId])
  const edgeIds = new Set<string>()

  const sourceNode = nodes.find(n => n.id === sourceNodeId)
  if (sourceNode?.parentId) {
    nodeIds.add(sourceNode.parentId)
  }

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
