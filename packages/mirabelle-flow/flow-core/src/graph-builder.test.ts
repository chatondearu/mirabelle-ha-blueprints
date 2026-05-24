import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { parseAutomationYaml } from './parser.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

describe('graph structure', () => {
  it('adds blueprint input nodes without separate lane layout', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    const inputs = doc.nodes.filter(n => n.kind === 'blueprint_input')
    expect(inputs.length).toBeGreaterThanOrEqual(3)
  })

  it('connects root to each trigger and adds reference edges for trigger conditions', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const root = doc.nodes.find(n => n.kind === 'root')
    const triggers = doc.nodes.filter(n => n.kind === 'trigger')
    expect(triggers.length).toBeGreaterThanOrEqual(2)

    for (const trigger of triggers) {
      expect(
        doc.edges.some(
          e =>
            e.source === root?.id
            && e.target === trigger.id
            && e.edgeKind !== 'reference',
        ),
      ).toBe(true)
    }

    const refs = doc.edges.filter(e => e.edgeKind === 'reference')
    expect(refs.length).toBeGreaterThanOrEqual(2)
  })
})
