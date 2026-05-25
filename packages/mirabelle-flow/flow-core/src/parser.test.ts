import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { parseAutomationYaml } from './parser.js'
import { serializeDocument } from './serializer.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

describe('parseAutomationYaml', () => {
  it('parses presence_based_lighting blueprint', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
    })

    expect(doc.kind).toBe('blueprint')
    expect(doc.blueprintMeta?.domain).toBe('automation')
    expect(doc.blueprintMeta?.inputs.length).toBeGreaterThanOrEqual(3)
    expect(doc.nodes.some(n => n.kind === 'trigger')).toBe(true)
    expect(doc.nodes.some(n => n.kind === 'choose')).toBe(true)
    expect(doc.nodes.some(n => n.kind === 'blueprint')).toBe(true)
    expect(doc.nodes.some(n => n.kind === 'blueprint_input')).toBe(true)
    expect(doc.nodes.some(n => (n.kind as string) === 'root')).toBe(false)
    const blueprint = doc.nodes.find(n => n.kind === 'blueprint')
    expect(blueprint?.data.simulationValues).toBeDefined()
    expect(doc.nodes.length).toBeGreaterThan(3)
  })

  it('parses create_schedule script blueprint', () => {
    const yaml = loadBlueprint('blueprints/scripts/create_schedule.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'create_schedule.yaml',
    })

    expect(doc.kind).toBe('blueprint')
    expect(doc.blueprintMeta?.domain).toBe('script')
    expect(doc.nodes.some(n => n.kind === 'action')).toBe(true)
  })

  it('preview mode substitutes inputs', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: true,
    })

    const actionNode = doc.nodes.find(
      n => n.kind === 'action' && typeof n.data.service === 'string',
    )
    expect(actionNode).toBeDefined()
    const target = actionNode?.data.target as { entity_id?: string } | undefined
    expect(target?.entity_id).toBe('light.test')
  })

  it('round-trip preserves yaml when not dirty', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { preview: false })
    expect(serializeDocument(doc).trimEnd()).toBe(yaml.trimEnd())
  })

  it('enriches action labels in preview mode', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: true,
    })
    const action = doc.nodes.find(
      n => n.kind === 'action' && n.label.includes('light.turn_on'),
    )
    expect(action?.label).toContain('→')
  })

  it('hides internal variables without external bindings', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })
    const vars = doc.nodes.filter(n => n.kind === 'variable')
    expect(vars.some(v => v.data.hidden === true)).toBe(true)
    expect(vars.some(v => v.data.hidden !== true)).toBe(true)
  })
})
