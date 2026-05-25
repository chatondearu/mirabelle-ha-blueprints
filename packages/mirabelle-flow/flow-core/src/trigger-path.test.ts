import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { parseAutomationYaml } from './parser.js'
import { getTriggerPathNodeIds } from './trigger-path.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

describe('getTriggerPathNodeIds', () => {
  it('excludes sibling trigger and blueprint nodes when focusing keypad trigger', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const keypad = doc.nodes.find(
      n => n.kind === 'trigger' && n.data.id === 'keypad_event',
    )
    expect(keypad).toBeDefined()

    const visible = getTriggerPathNodeIds(keypad!.id, doc.nodes, doc.edges)!
    expect(visible.has(keypad!.id)).toBe(true)
    expect(visible.has('blueprint')).toBe(true)

    const otherTrigger = doc.nodes.find(
      n => n.kind === 'trigger' && n.data.id === 'alarmo_state_change',
    )
    expect(otherTrigger).toBeDefined()
    expect(visible.has(otherTrigger!.id)).toBe(false)
  })

  it('shows shared automation path when triggers have no explicit branch reference', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    const trigger = doc.nodes.find(n => n.kind === 'trigger' && n.path === 'trigger/0')
    const visible = getTriggerPathNodeIds(trigger!.id, doc.nodes, doc.edges)!

    expect(visible.has('trigger_1')).toBe(false)
    expect(doc.nodes.some(n => n.kind === 'choose' && visible.has(n.id))).toBe(true)
  })
})
