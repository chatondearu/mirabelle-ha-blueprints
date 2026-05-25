import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { isConfigLayerNode } from '@mirabelle/flow-shared'

export function extractTriggerIdsFromCondition(data: Record<string, unknown>): string[] {
  const ids: string[] = []
  if (data.condition === 'trigger' && typeof data.id === 'string') {
    ids.push(data.id)
  }
  if (Array.isArray(data.conditions)) {
    for (const item of data.conditions) {
      if (item && typeof item === 'object') {
        ids.push(...extractTriggerIdsFromCondition(item as Record<string, unknown>))
      }
    }
  }
  return ids
}

function conditionReferencesTrigger(
  data: Record<string, unknown>,
  haTriggerId: string | undefined,
): boolean {
  if (haTriggerId) {
    if (extractTriggerIdsFromCondition(data).includes(haTriggerId)) {
      return true
    }
  }
  const template = data.value_template
  if (typeof template === 'string' && template.includes('trigger')) {
    return true
  }
  return false
}

function findEntryPointsForTrigger(
  trigger: FlowNode,
  nodes: FlowNode[],
  edges: FlowEdge[],
): FlowNode[] {
  const haTriggerId = typeof trigger.data.id === 'string' ? trigger.data.id : undefined
  const entryPoints = new Map<string, FlowNode>()

  for (const edge of edges) {
    if (edge.source === trigger.id && edge.edgeKind === 'reference') {
      const target = nodes.find(n => n.id === edge.target)
      if (target) {
        entryPoints.set(target.id, target)
      }
    }
  }

  for (const node of nodes) {
    if (node.kind !== 'condition') {
      continue
    }
    if (conditionReferencesTrigger(node.data, haTriggerId)) {
      entryPoints.set(node.id, node)
    }
  }

  return [...entryPoints.values()]
}

function addAncestors(
  nodeId: string,
  nodeById: Map<string, FlowNode>,
  active: Set<string>,
): void {
  let current = nodeById.get(nodeId)
  while (current?.parentId) {
    active.add(current.parentId)
    current = nodeById.get(current.parentId)
  }
}

function walkFlowDescendants(
  startIds: string[],
  edges: FlowEdge[],
  active: Set<string>,
): void {
  const flowEdges = edges.filter(e => e.edgeKind !== 'reference')
  const queue = [...startIds]
  while (queue.length > 0) {
    const id = queue.shift()!
    if (!active.has(id)) {
      active.add(id)
    }
    for (const edge of flowEdges) {
      if (edge.source === id && !active.has(edge.target)) {
        active.add(edge.target)
        queue.push(edge.target)
      }
    }
  }
}

/**
 * Node ids to show when focusing a single trigger's logic path.
 * Returns null when the trigger id is invalid (caller should show all nodes).
 */
export function getTriggerPathNodeIds(
  triggerId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): Set<string> | null {
  const trigger = nodes.find(n => n.id === triggerId && n.kind === 'trigger')
  if (!trigger) {
    return null
  }

  const nodeById = new Map(nodes.map(n => [n.id, n]))
  const active = new Set<string>([triggerId])

  for (const node of nodes) {
    if (isConfigLayerNode(node)) {
      active.add(node.id)
    }
  }

  const entryPoints = findEntryPointsForTrigger(trigger, nodes, edges)

  if (entryPoints.length === 0) {
    for (const node of nodes) {
      if (isConfigLayerNode(node)) {
        continue
      }
      if (node.kind === 'trigger' && node.id !== triggerId) {
        continue
      }
      active.add(node.id)
    }
    return active
  }

  const entryIds = entryPoints.map(n => n.id)
  walkFlowDescendants(entryIds, edges, active)
  for (const id of [...active]) {
    addAncestors(id, nodeById, active)
  }

  for (const node of nodes) {
    if (node.kind === 'trigger' && node.id !== triggerId) {
      active.delete(node.id)
    }
  }

  return active
}
