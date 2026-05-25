import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { getFocusedPath, getUpstreamPath } from './node-path.js'
import { parseAutomationYaml } from './parser.js'

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../../../')

function loadBlueprint(relPath: string): string {
  return readFileSync(join(repoRoot, relPath), 'utf-8')
}

describe('node-path', () => {
  it('upstream path from choose includes trigger entry', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    const choose = doc.nodes.find(n => n.kind === 'choose')
    const trigger = doc.nodes.find(n => n.kind === 'trigger')
    expect(choose).toBeDefined()
    expect(trigger).toBeDefined()

    const { nodeIds } = getUpstreamPath(choose!.id, doc.nodes, doc.edges)
    expect(nodeIds.has(trigger!.id)).toBe(true)
    expect(nodeIds.has(choose!.id)).toBe(true)
  })

  it('focused path on condition includes downstream choose', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    const cond = doc.nodes.find(n => n.path === 'condition/0')
    const choose = doc.nodes.find(n => n.kind === 'choose')
    expect(cond).toBeDefined()

    const { nodeIds } = getFocusedPath(cond!.id, doc.nodes, doc.edges)
    expect(nodeIds.has(cond!.id)).toBe(true)
    expect(nodeIds.has(choose!.id)).toBe(true)
  })
})
