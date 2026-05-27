import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { getTriggerPathNodeIds } from './trigger-path.js'

export interface NodePathResult {
  nodeIds: Set<string>
  edgeIds: Set<string>
}

function flowEdges(edges: FlowEdge[]): FlowEdge[] {
  return edges.filter(
    e =>
      e.edgeKind === 'flow'
      || e.edgeKind === undefined,
  )
}

const BINDING_EDGE_KINDS = new Set([
  'input_binding',
  'variable_binding',
])

function expandWithBindingNodes(
  base: Set<string>,
  edges: FlowEdge[],
): Set<string> {
  const active = new Set(base)
  for (const e of edges) {
    if (!e.edgeKind || !BINDING_EDGE_KINDS.has(e.edgeKind)) {
      continue
    }
    if (active.has(e.source) || active.has(e.target)) {
      active.add(e.source)
      active.add(e.target)
    }
  }
  return active
}

function buildAdjacency(edges: FlowEdge[]): Map<string, string[]> {
  const adj = new Map<string, string[]>()
  for (const e of edges) {
    const list = adj.get(e.source) ?? []
    list.push(e.target)
    adj.set(e.source, list)
  }
  return adj
}

function buildReverseAdjacency(edges: FlowEdge[]): Map<string, string[]> {
  const rev = new Map<string, string[]>()
  for (const e of edges) {
    const list = rev.get(e.target) ?? []
    list.push(e.source)
    rev.set(e.target, list)
  }
  return rev
}

export function collectPathEdges(nodeIds: Set<string>, edges: FlowEdge[]): Set<string> {
  const edgeIds = new Set<string>()
  for (const edge of edges) {
    if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
      edgeIds.add(edge.id)
    }
  }
  return edgeIds
}

/** Ancestors along flow edges (root → … → node), including the node. */
export function getUpstreamPathNodeIds(
  nodeId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): Set<string> {
  const active = new Set<string>([nodeId])
  const rev = buildReverseAdjacency(flowEdges(edges))
  const queue = [nodeId]

  while (queue.length > 0) {
    const id = queue.shift()!
    for (const parent of rev.get(id) ?? []) {
      if (!active.has(parent)) {
        active.add(parent)
        queue.push(parent)
      }
    }
  }

  return active
}

/** Descendants along flow edges (node → …), including the node. */
export function getDownstreamPathNodeIds(
  nodeId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): Set<string> {
  const active = new Set<string>([nodeId])
  const adj = buildAdjacency(flowEdges(edges))
  const queue = [nodeId]

  while (queue.length > 0) {
    const id = queue.shift()!
    for (const child of adj.get(id) ?? []) {
      if (!active.has(child)) {
        active.add(child)
        queue.push(child)
      }
    }
  }

  return active
}

/** Full parcours for focus mode (double-click). Triggers use branch-aware logic. */
export function getFocusedPathNodeIds(
  nodeId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): Set<string> {
  const node = nodes.find(n => n.id === nodeId)
  if (!node) {
    return new Set()
  }

  if (node.kind === 'trigger') {
    const base = getTriggerPathNodeIds(nodeId, nodes, edges) ?? new Set([nodeId])
    return expandWithBindingNodes(base, edges)
  }

  const upstream = getUpstreamPathNodeIds(nodeId, nodes, edges)
  const downstream = getDownstreamPathNodeIds(nodeId, nodes, edges)
  const base = new Set([...upstream, ...downstream])
  return expandWithBindingNodes(base, edges)
}

export function getUpstreamPath(
  nodeId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): NodePathResult {
  const nodeIds = getUpstreamPathNodeIds(nodeId, nodes, edges)
  return { nodeIds, edgeIds: collectPathEdges(nodeIds, edges) }
}

export function getFocusedPath(
  nodeId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): NodePathResult {
  const nodeIds = getFocusedPathNodeIds(nodeId, nodes, edges)
  return { nodeIds, edgeIds: collectPathEdges(nodeIds, edges) }
}
