import { describe, expect, it } from 'vitest'
import type { FlowNode } from './types.js'
import { FLOW_NODE_METRICS } from './layout.js'
import {
  estimateNodeSize,
  layoutGroupChildren,
  reconcileGroupLayouts,
} from './group-layout.js'

function child(id: string, kind: FlowNode['kind'], parentId: string): FlowNode {
  return {
    id,
    kind,
    label: id,
    path: id,
    data: {},
    parentId,
    layer: 'blueprint',
  }
}

describe('layoutGroupChildren', () => {
  it('uses fixed single-line height for action-like nodes', () => {
    const action = child('a', 'action', 'parent')
    const cond = child('c', 'condition', 'parent')
    expect(estimateNodeSize(action).height).toBe(FLOW_NODE_METRICS.cardSingleLineHeight)
    expect(estimateNodeSize(cond).height).toBe(FLOW_NODE_METRICS.cardSingleLineHeight)
  })

  it('stacks children without vertical overlap', () => {
    const children = [
      child('a', 'blueprint_input', 'parent'),
      child('b', 'blueprint_input', 'parent'),
      child('c', 'variable', 'parent'),
    ]
    const { positions, size } = layoutGroupChildren(children)

    const ordered = children.map(c => ({
      id: c.id,
      y: positions[c.id]!.y,
      h: estimateNodeSize(c).height,
    }))
    ordered.sort((a, b) => a.y - b.y)
    for (let i = 0; i < ordered.length - 1; i++) {
      expect(ordered[i]!.y + ordered[i]!.h).toBeLessThanOrEqual(ordered[i + 1]!.y)
    }
    expect(size.height).toBeGreaterThan(ordered[ordered.length - 1]!.y)
  })

  it('keeps padding around children and ignores transient renderSize hints', () => {
    const children = [
      child('a', 'action', 'parent'),
      child('b', 'condition', 'parent'),
    ]
    children[0]!.data.renderSize = { width: 320, height: 70 }
    const { positions, size } = layoutGroupChildren(children, { headerHeight: 40 })

    expect(positions.a!.x).toBeGreaterThan(0)
    expect(positions.a!.y).toBeGreaterThan(40)
    expect(size.width).toBeLessThan(320)
    expect(size.height).toBeGreaterThan(positions.b!.y)
  })

  it('expands parent width when child subtree reaches grandchild depth', () => {
    const c1 = child('c1', 'action', 'parent')
    const c2 = child('c2', 'action', 'parent')
    const gc = child('gc1', 'action', 'c1')
    const ggc = child('ggc1', 'action', 'gc1')
    const shallow = layoutGroupChildren([c1, c2], { headerHeight: 40 })
    const deep = layoutGroupChildren([c1, c2, gc, ggc], { headerHeight: 40 })
    expect(deep.size.width).toBeGreaterThan(shallow.size.width)
  })
})

describe('reconcileGroupLayouts', () => {
  it('shrinks variables group when hidden children are excluded', () => {
    const parent: FlowNode = {
      id: 'variables',
      kind: 'variables',
      label: 'Variables',
      path: 'variables',
      data: { isGroup: true },
      layer: 'blueprint',
    }
    const visible = child('v1', 'variable', 'variables')
    const hidden = child('v2', 'variable', 'variables')
    hidden.data.hidden = true
    const nodes = [parent, visible, hidden]
    const baseLayout = { variables: { x: 0, y: 0 } }

    const all = reconcileGroupLayouts(nodes, baseLayout, () => true)
    const filtered = reconcileGroupLayouts(nodes, baseLayout, n => n.data.hidden !== true)

    expect(filtered.groupSizes.variables!.height).toBeLessThan(all.groupSizes.variables!.height)
    expect(filtered.layout.v2).toBeUndefined()
    expect(filtered.layout.v1).toBeDefined()
  })
})
