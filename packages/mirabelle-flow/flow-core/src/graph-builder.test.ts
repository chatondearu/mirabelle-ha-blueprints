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
  it('keeps blueprint inputs on meta node only', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    expect(doc.nodes.some(n => n.kind === 'blueprint_input')).toBe(false)
    const meta = doc.nodes.find(n => n.kind === 'blueprint_meta')
    expect(meta?.data.inputs).toBeDefined()
    expect(meta?.data.simulationValues).toBeDefined()
  })

  it('creates a variables list node with one item per YAML variable', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const varsNode = doc.nodes.find(n => n.kind === 'variables')
    expect(varsNode).toBeDefined()
    const items = varsNode?.data.items as Array<{ key: string }> | undefined
    expect(items?.length).toBeGreaterThan(5)
    expect(items?.some(item => item.key === 'language')).toBe(true)
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
    expect(services.length).toBeGreaterThan(2)
  })

  it('connects root to each trigger and adds reference edges', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const root = doc.nodes.find(n => n.kind === 'root')
    const triggers = doc.nodes.filter(n => n.kind === 'trigger')
    for (const trigger of triggers) {
      expect(
        doc.edges.some(
          e =>
            e.source === root?.id
            && e.target === trigger.id
            && e.edgeKind === 'flow',
        ),
      ).toBe(true)
    }

    const refs = doc.edges.filter(e => e.edgeKind === 'reference')
    expect(refs.length).toBeGreaterThanOrEqual(2)
  })

  it('creates choose option handles and no synthetic condition subnodes', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })
    const chooseNode = doc.nodes.find(n => n.kind === 'choose')
    expect(chooseNode).toBeDefined()
    const options = chooseNode?.data.options as Array<{ key: string }> | undefined
    expect(options?.length).toBeGreaterThanOrEqual(1)
    expect(
      doc.edges.some(e => e.source === chooseNode?.id && e.sourceHandle?.startsWith('opt-')),
    ).toBe(true)
  })
})
