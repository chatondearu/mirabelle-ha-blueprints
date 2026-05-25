import type { FlowNode, FlowNodeKind, FlowPosition } from './types.js'

export interface GroupSize {
  width: number
  height: number
}

export interface GroupLayoutResult {
  layout: Record<string, FlowPosition>
  groupSizes: Record<string, GroupSize>
}

/** Estimated child footprint on the canvas (px). */
export const NODE_LAYOUT_SIZES: Partial<Record<FlowNodeKind, { width: number, height: number }>> = {
  blueprint_input: { width: 200, height: 80 },
  variable: { width: 184, height: 60 },
  choose_option: { width: 200, height: 36 },
  action: { width: 208, height: 56 },
  condition: { width: 208, height: 68 },
  ha_block: { width: 200, height: 44 },
  sequence: { width: 200, height: 48 },
  parallel: { width: 200, height: 48 },
  repeat: { width: 200, height: 48 },
  choose: { width: 220, height: 52 },
  delay: { width: 180, height: 52 },
  wait: { width: 180, height: 52 },
}

export const GROUP_LAYOUT = {
  headerHeight: 56,
  padding: 16,
  childGap: 12,
  minWidth: 220,
  minHeight: 88,
} as const

export function estimateNodeSize(node: FlowNode): { width: number, height: number } {
  const stored = node.data.groupSize as GroupSize | undefined
  if (stored && stored.width > 0 && stored.height > 0) {
    return { width: stored.width, height: stored.height }
  }
  return NODE_LAYOUT_SIZES[node.kind] ?? { width: 184, height: 56 }
}

export function isLayoutParentNode(node: FlowNode, allNodes: FlowNode[] = []): boolean {
  if (
    node.kind === 'blueprint'
    || node.kind === 'variables'
    || node.data.isGroup === true
    || node.data.isContainer === true
  ) {
    return true
  }
  return allNodes.some(child => child.parentId === node.id)
}

export function parentDepth(node: FlowNode, nodes: FlowNode[]): number {
  let depth = 0
  let current: FlowNode | undefined = node
  while (current?.parentId) {
    depth += 1
    current = nodes.find(n => n.id === current!.parentId)
  }
  return depth
}

/**
 * Stack children vertically inside a parent with non-overlapping positions.
 */
export function layoutGroupChildren(
  children: FlowNode[],
  options: {
    headerHeight?: number
    padding?: number
    childGap?: number
    minWidth?: number
  } = {},
): { positions: Record<string, FlowPosition>, size: GroupSize } {
  const headerHeight = options.headerHeight ?? GROUP_LAYOUT.headerHeight
  const padding = options.padding ?? GROUP_LAYOUT.padding
  const childGap = options.childGap ?? GROUP_LAYOUT.childGap
  const minWidth = options.minWidth ?? GROUP_LAYOUT.minWidth

  const positions: Record<string, FlowPosition> = {}
  let y = headerHeight
  let maxChildWidth = 0

  const ordered = [...children].sort(
    (a, b) =>
      (typeof a.data.layoutOrder === 'number' ? a.data.layoutOrder : 0)
      - (typeof b.data.layoutOrder === 'number' ? b.data.layoutOrder : 0),
  )

  for (const child of ordered) {
    const size = estimateNodeSize(child)
    positions[child.id] = { x: padding, y }
    maxChildWidth = Math.max(maxChildWidth, size.width)
    y += size.height + childGap
  }

  const width = Math.max(minWidth, maxChildWidth + padding * 2)
  const height = Math.max(
    GROUP_LAYOUT.minHeight,
    children.length > 0 ? y - childGap + padding : headerHeight + padding,
  )

  return { positions, size: { width, height } }
}

/**
 * Recompute parent bounds and child positions (e.g. when filtering hidden variables).
 */
export function reconcileGroupLayouts(
  nodes: FlowNode[],
  baseLayout: Record<string, FlowPosition>,
  isChildVisible: (node: FlowNode) => boolean = () => true,
): GroupLayoutResult {
  const layout = { ...baseLayout }
  const groupSizes: Record<string, GroupSize> = {}

  const parents = nodes
    .filter(n => isLayoutParentNode(n, nodes))
    .sort((a, b) => parentDepth(b, nodes) - parentDepth(a, nodes))

  for (const parent of parents) {
    const children = nodes.filter(
      n => n.parentId === parent.id && isChildVisible(n),
    )
    const headerHeight =
      typeof parent.data.layoutHeaderHeight === 'number'
        ? parent.data.layoutHeaderHeight
        : undefined
    const { positions, size } = layoutGroupChildren(children, { headerHeight })
    groupSizes[parent.id] = size
    for (const [childId, pos] of Object.entries(positions)) {
      layout[childId] = pos
    }
  }

  return { layout, groupSizes }
}
