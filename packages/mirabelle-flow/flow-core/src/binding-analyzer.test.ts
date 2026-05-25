import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { analyzeBindings } from './binding-analyzer.js'
import { parseAutomationYaml } from './parser.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

describe('analyzeBindings', () => {
  it('creates input_binding edges from inputs node to consumers', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'frient_keypad_with_alarmo.yaml',
      preview: false,
    })

    expect(doc.nodes.some(n => n.kind === 'blueprint_input')).toBe(false)
    const inputBindings = doc.edges.filter(e => e.edgeKind === 'input_binding')
    expect(inputBindings.length).toBeGreaterThan(0)
    const inputsNode = doc.nodes.find(n => n.kind === 'inputs' || n.kind === 'inputs_variables')
    expect(inputBindings.some(e => e.source === inputsNode?.id)).toBe(true)
  })

  it('creates variable_binding edges for template references', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'frient_keypad_with_alarmo.yaml',
      preview: false,
    })

    const varsNode = doc.nodes.find(n => n.kind === 'variables' || n.kind === 'inputs_variables')
    expect(varsNode).toBeDefined()

    const varBindings = doc.edges.filter(e => e.edgeKind === 'variable_binding')
    expect(varBindings.length).toBeGreaterThan(0)
  })
})

describe('analyzeBindings unit', () => {
  it('links input refs in node data', () => {
    const nodes = [
      {
        id: 'inputs',
        kind: 'inputs' as const,
        label: 'Inputs',
        path: 'inputs',
        data: { items: [{ key: 'sensor', label: 'sensor' }] },
      },
      {
        id: 'trigger_0',
        kind: 'trigger' as const,
        label: 'T',
        path: 'trigger/0',
        data: { entity_id: { __input: 'sensor' } },
      },
    ]
    const edges = analyzeBindings(nodes)
    expect(edges.some(e => e.edgeKind === 'input_binding' && e.label === 'sensor')).toBe(
      true,
    )
  })
})
