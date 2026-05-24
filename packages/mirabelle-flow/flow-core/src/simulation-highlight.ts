import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { extractTriggerIdsFromCondition } from './trigger-path.js'

/** Branch / node ids that would run for a given trigger under simulation (static). */
export function getSimulationActiveNodeIds(
  triggerId: string,
  nodes: FlowNode[],
  edges: FlowEdge[],
): Set<string> {
  const active = new Set<string>()
  const trigger = nodes.find(n => n.id === triggerId && n.kind === 'trigger')
  if (!trigger) {
    return active
  }

  const haId = typeof trigger.data.id === 'string' ? trigger.data.id : undefined
  active.add(triggerId)

  for (const node of nodes) {
    if (node.kind !== 'condition') {
      continue
    }
    const refs = extractTriggerIdsFromCondition(node.data)
    const template = node.data.value_template
    const templateRefsTrigger =
      typeof template === 'string'
      && (template.includes('trigger.') || template.includes('trigger '))

    if ((haId && refs.includes(haId)) || (!haId && templateRefsTrigger)) {
      active.add(node.id)
      walkDownstream(node.id, edges, active, nodes)
      addAncestors(node, nodes, active)
    }
  }

  return active
}

function walkDownstream(
  startId: string,
  edges: FlowEdge[],
  active: Set<string>,
  nodes: FlowNode[],
): void {
  const flowEdges = edges.filter(
    e => e.edgeKind === 'flow' || e.edgeKind === undefined,
  )
  const queue = [startId]
  while (queue.length > 0) {
    const id = queue.shift()!
    for (const edge of flowEdges) {
      if (edge.source === id && !active.has(edge.target)) {
        active.add(edge.target)
        queue.push(edge.target)
      }
    }
  }
}

function addAncestors(node: FlowNode, nodes: FlowNode[], active: Set<string>): void {
  let parentId = node.parentId
  while (parentId) {
    active.add(parentId)
    const parent = nodes.find(n => n.id === parentId)
    parentId = parent?.parentId
  }
}
