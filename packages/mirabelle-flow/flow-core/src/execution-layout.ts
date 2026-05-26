import type { FlowEdge, FlowNode, FlowPosition } from '@mirabelle/flow-shared'
import {
  FLOW_LAYOUT,
  estimateNodeSize,
  isConfigLayerNode,
} from '@mirabelle/flow-shared'

function isFlowEdge(edge: FlowEdge): boolean {
  return edge.edgeKind === 'flow' || edge.edgeKind === undefined
}

function laneSeedFromBranchKey(branchKey: string | undefined): number {
  if (!branchKey) {
    return 0
  }
  if (branchKey === 'opt-default' || branchKey === 'if-else') {
    return 9000
  }
  const opt = branchKey.match(/^opt-(\d+)$/)
  if (opt) {
    return Number(opt[1])
  }
  const ifb = branchKey.match(/^if-(\d+)$/)
  if (ifb) {
    return Number(ifb[1])
  }
  return 0
}

function resolveSourceColumn(
  sourceId: string,
  column: Map<string, number>,
  rootIds: Set<string>,
  nodeById: Map<string, FlowNode>,
): number | undefined {
  if (rootIds.has(sourceId)) {
    return column.get(sourceId)
  }
  const src = nodeById.get(sourceId)
  if (!src?.parentId) {
    return undefined
  }
  const parent = nodeById.get(src.parentId)
  if (parent && rootIds.has(parent.id)) {
    return column.get(parent.id)
  }
  return undefined
}

function assignColumns(
  execRoots: FlowNode[],
  allNodes: FlowNode[],
  flowEdges: FlowEdge[],
): Map<string, number> {
  const column = new Map<string, number>()
  const rootIds = new Set(execRoots.map(n => n.id))
  const nodeById = new Map(allNodes.map(n => [n.id, n]))

  const triggers = execRoots.filter(n => n.kind === 'trigger')
  for (const t of triggers) {
    column.set(t.id, 0)
  }

  for (const n of execRoots) {
    if (!column.has(n.id)) {
      column.set(n.id, 0)
    }
  }

  let changed = true
  let passes = 0
  while (changed && passes < execRoots.length + 5) {
    changed = false
    passes += 1
    for (const e of flowEdges) {
      if (!isFlowEdge(e) || !rootIds.has(e.target)) {
        continue
      }
      const sourceCol = resolveSourceColumn(
        e.source,
        column,
        rootIds,
        nodeById,
      )
      if (sourceCol === undefined) {
        continue
      }
      const nextCol = sourceCol + 1
      const prev = column.get(e.target)
      if (prev === undefined || nextCol > prev) {
        column.set(e.target, nextCol)
        changed = true
      }
    }
    for (const e of flowEdges) {
      if (!isFlowEdge(e) || !rootIds.has(e.source) || !rootIds.has(e.target)) {
        continue
      }
      const sourceCol = column.get(e.source) ?? 0
      const nextCol = sourceCol + 1
      const prev = column.get(e.target)
      if (prev === undefined || nextCol > prev) {
        column.set(e.target, nextCol)
        changed = true
      }
    }
  }

  return column
}

function assignLanes(
  execRoots: FlowNode[],
  allNodes: FlowNode[],
  flowEdges: FlowEdge[],
): Map<string, number> {
  const lane = new Map<string, number>()
  const rootIds = new Set(execRoots.map(n => n.id))
  const nodeById = new Map(allNodes.map(n => [n.id, n]))

  for (const e of flowEdges) {
    if (!isFlowEdge(e) || !rootIds.has(e.target)) {
      continue
    }
    const src = nodeById.get(e.source)
    if (!src?.parentId) {
      continue
    }
    if (src.kind !== 'condition' && src.kind !== 'choose_option') {
      continue
    }
    const parent = nodeById.get(src.parentId)
    if (parent?.kind !== 'choose' && parent?.data.blockKey !== 'if') {
      continue
    }
    const seed =
      laneSeedFromBranchKey(
        (src.data.branchKey ?? src.data.key) as string | undefined,
      )
    const existing = lane.get(e.target)
    if (existing === undefined || seed < existing) {
      lane.set(e.target, seed)
    }
  }

  let nextLane = 0
  const triggers = execRoots.filter(n => n.kind === 'trigger')
  for (const t of triggers) {
    if (!lane.has(t.id)) {
      lane.set(t.id, nextLane++)
    }
    nextLane = Math.max(nextLane, (lane.get(t.id) ?? 0) + 1)
  }

  const sorted = [...execRoots].sort(
    (a, b) => (lane.get(a.id) ?? 0) - (lane.get(b.id) ?? 0),
  )

  for (const n of sorted) {
    if (lane.has(n.id)) {
      continue
    }
    const preds = flowEdges
      .filter(e => e.target === n.id && isFlowEdge(e) && rootIds.has(e.source))
      .map(e => e.source)
    if (preds.length === 0) {
      lane.set(n.id, nextLane++)
      continue
    }
    const predLanes = preds
      .map(p => lane.get(p))
      .filter((l): l is number => l !== undefined)
    lane.set(n.id, predLanes.length > 0 ? Math.min(...predLanes) : nextLane++)
  }

  return lane
}

function resolveOverlaps(
  positions: Map<string, FlowPosition>,
  nodes: FlowNode[],
  padding: number,
): void {
  const byColumn = new Map<number, FlowNode[]>()
  for (const n of nodes) {
    const pos = positions.get(n.id)
    if (!pos) {
      continue
    }
    const col = Math.round((pos.x - FLOW_LAYOUT.startX) / FLOW_LAYOUT.horizontalGap)
    const list = byColumn.get(col) ?? []
    list.push(n)
    byColumn.set(col, list)
  }

  for (const group of byColumn.values()) {
    group.sort((a, b) => (positions.get(a.id)?.y ?? 0) - (positions.get(b.id)?.y ?? 0))
    for (let i = 1; i < group.length; i++) {
      const prev = group[i - 1]!
      const curr = group[i]!
      const prevPos = positions.get(prev.id)!
      const currPos = positions.get(curr.id)!
      const prevBottom = prevPos.y + estimateNodeSize(prev).height + padding
      if (currPos.y < prevBottom) {
        positions.set(curr.id, { ...currPos, y: prevBottom })
      }
    }
  }
}

/**
 * Place execution-band root nodes left-to-right by column, stacked by branch lane.
 */
export function layoutExecutionBand(
  nodes: FlowNode[],
  edges: FlowEdge[],
  execY: number,
): Record<string, FlowPosition> {
  const layout: Record<string, FlowPosition> = {}
  const execRoots = nodes.filter(
    n => !n.parentId && !isConfigLayerNode(n),
  )
  if (execRoots.length === 0) {
    return layout
  }

  const flowEdges = edges.filter(isFlowEdge)
  const column = assignColumns(execRoots, nodes, flowEdges)
  const lane = assignLanes(execRoots, nodes, flowEdges)

  const byColumn = new Map<number, FlowNode[]>()
  for (const n of execRoots) {
    const col = column.get(n.id) ?? 0
    const list = byColumn.get(col) ?? []
    list.push(n)
    byColumn.set(col, list)
  }

  const laneGap = 16
  for (const [col, group] of byColumn) {
    group.sort(
      (a, b) =>
        (lane.get(a.id) ?? 0) - (lane.get(b.id) ?? 0)
        || a.id.localeCompare(b.id),
    )
    let y = execY
    for (const n of group) {
      layout[n.id] = {
        x: FLOW_LAYOUT.startX + col * FLOW_LAYOUT.horizontalGap,
        y,
      }
      y += estimateNodeSize(n).height + laneGap
    }
  }

  const positions = new Map(Object.entries(layout).map(([id, pos]) => [id, pos]))
  resolveOverlaps(positions, execRoots, laneGap)
  for (const [id, pos] of positions) {
    layout[id] = pos
  }

  return layout
}
