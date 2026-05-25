import { describe, expect, it } from 'vitest'
import type { FlowEdge, FlowNode } from '@mirabelle/flow-shared'
import { findBranchExitNode } from './flow-endpoints.js'

function node(
  id: string,
  kind: FlowNode['kind'],
  parentId?: string,
  data: Record<string, unknown> = {},
): FlowNode {
  return {
    id,
    kind,
    label: id,
    path: id,
    data,
    parentId,
    layer: 'automation',
  }
}

describe('findBranchExitNode', () => {
  it('returns the default marker when present', () => {
    const choose = node('choose', 'choose', undefined, { isContainer: true })
    const marker = node('def', 'choose_option', 'choose', {
      key: 'opt-default',
      layoutOrder: 9000,
    })
    const cond = node('c0', 'condition', 'choose', {
      branchKey: 'opt-0',
      layoutOrder: 0,
    })
    const nodes = [choose, marker, cond]
    expect(findBranchExitNode(nodes, choose, 'opt-default')?.id).toBe('def')
    expect(findBranchExitNode(nodes, choose, 'opt-0')?.id).toBe('c0')
  })
})
