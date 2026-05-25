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
  it('keeps blueprint inputs as child nodes under blueprint parent', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    expect(doc.nodes.some(n => n.kind === 'blueprint_input')).toBe(true)
    expect(doc.nodes.some(n => (n.kind as string) === 'root')).toBe(false)
    const blueprint = doc.nodes.find(n => n.kind === 'blueprint')
    expect(blueprint?.data.isGroup).toBe(true)
    const inputs = doc.nodes.filter(n => n.kind === 'blueprint_input')
    expect(inputs.length).toBeGreaterThan(0)
    expect(inputs.every(n => n.parentId === blueprint?.id)).toBe(true)
    expect(doc.edges.some(e => e.edgeKind === 'flow' && e.source === blueprint?.id)).toBe(false)
  })

  it('creates variable child nodes under variables parent', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const varsParent = doc.nodes.find(n => n.kind === 'variables')
    expect(varsParent).toBeDefined()
    const varChildren = doc.nodes.filter(n => n.kind === 'variable')
    expect(varChildren.length).toBeGreaterThan(0)
    expect(varChildren.every(n => n.parentId === varsParent?.id)).toBe(true)
  })

  it('expands choose branches into action nodes', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'frient_keypad_with_alarmo.yaml',
      preview: true,
    })

    const services = doc.nodes.filter(
      n => n.kind === 'action' && typeof n.data.service === 'string',
    )
    // actions may live inside HA container parents
    expect(services.length).toBeGreaterThan(2)
  })

  it('does not connect config nodes to triggers with flow edges', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const blueprint = doc.nodes.find(n => n.kind === 'blueprint')
    const triggers = doc.nodes.filter(n => n.kind === 'trigger')
    for (const trigger of triggers) {
      expect(
        doc.edges.some(
          e =>
            (e.source === blueprint?.id || e.source === 'variables')
            && e.target === trigger.id
            && e.edgeKind === 'flow',
        ),
      ).toBe(false)
    }

    const refs = doc.edges.filter(e => e.edgeKind === 'reference')
    expect(refs.length).toBeGreaterThanOrEqual(2)
  })

  it('creates choose as container with option child nodes', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })
    const chooseNode = doc.nodes.find(n => n.kind === 'choose')
    expect(chooseNode?.data.isContainer).toBe(true)
    const options = doc.nodes.filter(n => n.kind === 'choose_option')
    expect(options.length).toBeGreaterThan(0)
    expect(options.every(n => n.parentId === chooseNode?.id)).toBe(true)
  })
})
