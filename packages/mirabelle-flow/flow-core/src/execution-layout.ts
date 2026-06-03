import type { FlowEdge, FlowNode, FlowPosition } from '@mirabelle/flow-shared'
import {
  FLOW_LAYOUT,
  FLOW_NODE_METRICS,
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

function resolveSourceRootId(
  sourceId: string,
  rootIds: Set<string>,
  nodeById: Map<string, FlowNode>,
): string | undefined {
  if (rootIds.has(sourceId)) {
    return sourceId
  }
  const src = nodeById.get(sourceId)
  if (!src?.parentId) {
    return undefined
  }
  const parent = nodeById.get(src.parentId)
  if (parent && rootIds.has(parent.id)) {
    return parent.id
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

  for (const n of execRoots) {
    if (column.has(n.id)) {
      continue
    }
    if (n.kind === 'trigger') {
      column.set(n.id, 0)
      continue
    }
    column.set(n.id, 1)
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

function boxesOverlap(
  a: { x: number, y: number, w: number, h: number },
  b: { x: number, y: number, w: number, h: number },
  gap: number,
): boolean {
  return (
    a.x < b.x + b.w + gap
    && a.x + a.w + gap > b.x
    && a.y < b.y + b.h + gap
    && a.y + a.h + gap > b.y
  )
}

function resolveInterColumnOverlaps(
  positions: Map<string, FlowPosition>,
  nodes: FlowNode[],
  gap: number,
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

  const cols = [...byColumn.keys()].sort((a, b) => a - b)
  for (let ci = 1; ci < cols.length; ci++) {
    const left = byColumn.get(cols[ci - 1]!) ?? []
    const right = byColumn.get(cols[ci]!) ?? []
    let requiredShift = 0

    for (const ln of left) {
      const lp = positions.get(ln.id)
      if (!lp) {
        continue
      }
      const ls = estimateNodeSize(ln)
      const lb = { x: lp.x, y: lp.y, w: ls.width, h: ls.height }

      for (const rn of right) {
        const rp = positions.get(rn.id)
        if (!rp) {
          continue
        }
        const rs = estimateNodeSize(rn)
        const rb = {
          x: rp.x,
          y: rp.y + requiredShift,
          w: rs.width,
          h: rs.height,
        }
        if (!boxesOverlap(lb, rb, gap)) {
          continue
        }
        const overlapShift = lb.y + lb.h + gap - rb.y
        if (overlapShift > requiredShift) {
          requiredShift = overlapShift
        }
      }
    }

    if (requiredShift > 0) {
      for (const rn of right) {
        const rp = positions.get(rn.id)
        if (!rp) {
          continue
        }
        positions.set(rn.id, { ...rp, y: rp.y + requiredShift })
      }
    }
  }
}

function orderColumnsWithBarycenter(
  byColumn: Map<number, FlowNode[]>,
  column: Map<string, number>,
  lane: Map<string, number>,
  allNodes: FlowNode[],
  flowEdges: FlowEdge[],
): void {
  const nodeById = new Map(allNodes.map(n => [n.id, n]))
  const rootIds = new Set(
    [...byColumn.values()].flat().map(n => n.id),
  )
  const sortedCols = [...byColumn.keys()].sort((a, b) => a - b)
  const rankById = new Map<string, number>()

  for (const col of sortedCols) {
    const group = byColumn.get(col)
    if (!group) {
      continue
    }

    const barycenterFor = (nodeId: string): number | undefined => {
      const incomingRanks = flowEdges
        .filter(e => isFlowEdge(e) && e.target === nodeId)
        .map((e) => {
          const srcCol = resolveSourceColumn(
            e.source,
            column,
            rootIds,
            nodeById,
          )
          if (srcCol === undefined || srcCol >= col) {
            return undefined
          }
          const srcRootId = resolveSourceRootId(e.source, rootIds, nodeById)
          if (!srcRootId) {
            return undefined
          }
          return rankById.get(srcRootId)
        })
        .filter((r): r is number => r !== undefined)

      if (incomingRanks.length === 0) {
        return undefined
      }
      return incomingRanks.reduce((sum, n) => sum + n, 0) / incomingRanks.length
    }

    group.sort((a, b) => {
      const baryA = barycenterFor(a.id)
      const baryB = barycenterFor(b.id)
      if (baryA !== undefined && baryB !== undefined && baryA !== baryB) {
        return baryA - baryB
      }
      if (baryA !== undefined && baryB === undefined) {
        return -1
      }
      if (baryA === undefined && baryB !== undefined) {
        return 1
      }
      return (
        (lane.get(a.id) ?? 0) - (lane.get(b.id) ?? 0)
        || a.id.localeCompare(b.id)
      )
    })

    group.forEach((n, idx) => {
      rankById.set(n.id, idx)
    })
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

  orderColumnsWithBarycenter(byColumn, column, lane, nodes, flowEdges)

  const laneGap = FLOW_NODE_METRICS.executionLaneGap
  for (const [col, group] of byColumn) {
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
  resolveInterColumnOverlaps(positions, execRoots, laneGap)
  for (const [id, pos] of positions) {
    layout[id] = pos
  }

  return layout
}
