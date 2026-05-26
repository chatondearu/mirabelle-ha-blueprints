import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { estimateNodeSize, isConfigLayerNode } from '@mirabelle/flow-shared'
import { parseAutomationYaml } from './parser.js'

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
