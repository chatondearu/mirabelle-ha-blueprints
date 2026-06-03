import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { estimateNodeSize, isConfigLayerNode, type FlowNode } from '@mirabelle/flow-shared'
import { parseAutomationYaml } from './parser.js'
import { layoutExecutionBand } from './execution-layout.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

function boxesOverlap(
  a: { x: number, y: number, w: number, h: number },
  b: { x: number, y: number, w: number, h: number },
  gap = 4,
): boolean {
  return (
    a.x < b.x + b.w + gap
    && a.x + a.w + gap > b.x
    && a.y < b.y + b.h + gap
    && a.y + a.h + gap > b.y
  )
}

describe('layoutExecutionBand', () => {
  it('orders target column by predecessor barycenter to reduce crossings', () => {
    const nodes: FlowNode[] = [
      {
        id: 't-a',
        kind: 'trigger',
        label: 'A',
        path: 'trigger/0',
        data: {},
        layer: 'automation',
      },
      {
        id: 't-b',
        kind: 'trigger',
        label: 'B',
        path: 'trigger/1',
        data: {},
        layer: 'automation',
      },
      {
        id: 'n-c',
        kind: 'action',
        label: 'C',
        path: 'action/0',
        data: {},
        layer: 'automation',
      },
      {
        id: 'n-d',
        kind: 'action',
        label: 'D',
        path: 'action/1',
        data: {},
        layer: 'automation',
      },
    ]
    const edges = [
      { id: 'e1', source: 't-a', target: 'n-d', edgeKind: 'flow' as const },
      { id: 'e2', source: 't-b', target: 'n-c', edgeKind: 'flow' as const },
    ]
    const layout = layoutExecutionBand(nodes, edges, 120)
    expect(layout['n-d']!.y).toBeLessThan(layout['n-c']!.y)
  })

  it('keeps deterministic ordering across repeated layout passes', () => {
    const nodes: FlowNode[] = [
      { id: 't1', kind: 'trigger', label: 'T1', path: 'trigger/0', data: {}, layer: 'automation' },
      { id: 't2', kind: 'trigger', label: 'T2', path: 'trigger/1', data: {}, layer: 'automation' },
      { id: 'a1', kind: 'action', label: 'A1', path: 'action/0', data: {}, layer: 'automation' },
      { id: 'a2', kind: 'action', label: 'A2', path: 'action/1', data: {}, layer: 'automation' },
    ]
    const edges = [
      { id: 'e1', source: 't1', target: 'a1', edgeKind: 'flow' as const },
      { id: 'e2', source: 't2', target: 'a2', edgeKind: 'flow' as const },
    ]
    const first = layoutExecutionBand(nodes, edges, 100)
    const second = layoutExecutionBand(nodes, edges, 100)
    expect(second).toEqual(first)
  })

  it('places frient execution roots without overlapping boxes', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const execRoots = doc.nodes.filter(n => !n.parentId && !isConfigLayerNode(n))
    const boxes = execRoots.map((n) => {
      const pos = doc.layout[n.id]!
      const size = estimateNodeSize(n)
      return { id: n.id, x: pos.x, y: pos.y, w: size.width, h: size.height }
    })

    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        expect(
          boxesOverlap(boxes[i]!, boxes[j]!),
          `overlap ${boxes[i]!.id} vs ${boxes[j]!.id}`,
        ).toBe(false)
      }
    }
  })

  it('increases column along a trigger-to-action chain', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: false,
    })

    const trigger = doc.nodes.find(n => n.kind === 'trigger')
    const choose = doc.nodes.find(n => n.kind === 'choose')
    expect(trigger).toBeDefined()
    expect(choose).toBeDefined()
    expect(doc.layout[choose!.id]!.x).toBeGreaterThan(doc.layout[trigger!.id]!.x)
  })

  it('places living-area choose after triggers with incoming flow', () => {
    const yaml = loadBlueprint(
      'blueprints/automations/living-area-adaptive-lighting.yaml',
    )
    const doc = parseAutomationYaml(yaml, {
      source: 'living-area-adaptive-lighting.yaml',
      preview: true,
    })

    const triggers = doc.nodes.filter(n => n.kind === 'trigger' && !n.parentId)
    const choose = doc.nodes.find(
      n => n.kind === 'choose' && n.path === 'action/0/if/then/sequence/0',
    )
    expect(choose).toBeDefined()
    expect(triggers.length).toBeGreaterThan(0)

    const flowIn = doc.edges.some(
      e =>
        e.target === choose!.id
        && (e.edgeKind === 'flow' || e.edgeKind === undefined),
    )
    expect(flowIn).toBe(true)

    const triggerX = Math.min(...triggers.map(t => doc.layout[t.id]!.x))
    expect(doc.layout[choose!.id]!.x).toBeGreaterThan(triggerX)
  })

  it('uses multiple columns for choose with branch actions', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: false,
    })

    const choose = doc.nodes.find(n => n.kind === 'choose')
    const turnOn = doc.nodes.find(
      n =>
        n.kind === 'action'
        && typeof n.data.service === 'string'
        && n.data.service.includes('turn_on'),
    )
    expect(choose).toBeDefined()
    expect(turnOn).toBeDefined()
    expect(doc.layout[turnOn!.id]!.x).toBeGreaterThan(doc.layout[choose!.id]!.x)
  })
})
