import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { estimateNodeSize } from '@mirabelle/flow-shared'
import { parseAutomationYaml } from './parser.js'
import { extractTriggerIdsFromCondition } from './trigger-path.js'

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

  it('does not create target/data ha_block children under service actions', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const serviceActions = doc.nodes.filter(
      n => n.kind === 'action' && typeof n.data.service === 'string',
    )
    expect(serviceActions.length).toBeGreaterThan(0)

    const detailBlocks = doc.nodes.filter(
      n =>
        n.kind === 'ha_block'
        && n.parentId
        && serviceActions.some(a => a.id === n.parentId),
    )
    expect(detailBlocks.length).toBe(0)
    expect(serviceActions.every(a => a.data.isContainer !== true)).toBe(true)
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

  it('connects every root trigger to the default execution entry when unassigned', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })

    const globalCondition = doc.nodes.find(n => n.path === 'condition/0')
    expect(globalCondition).toBeDefined()

    const triggers = doc.nodes.filter(n => n.kind === 'trigger' && !n.parentId)
    expect(triggers.length).toBe(2)

    for (const trigger of triggers) {
      expect(
        doc.edges.some(
          e =>
            e.source === trigger.id
            && e.target === globalCondition!.id
            && (e.edgeKind === 'flow' || e.edgeKind === undefined),
        ),
      ).toBe(true)
    }
  })

  it('routes triggers with explicit condition: trigger id to their branch conditions', () => {
    const yaml = loadBlueprint('blueprints/automations/frient_keypad_with_alarmo.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'frient_keypad_with_alarmo.yaml' })

    const keypad = doc.nodes.find(
      n => n.kind === 'trigger' && n.data.id === 'keypad_event',
    )
    const alarmo = doc.nodes.find(
      n => n.kind === 'trigger' && n.data.id === 'alarmo_state_change',
    )
    expect(keypad).toBeDefined()
    expect(alarmo).toBeDefined()

    const keypadCond = doc.nodes.find(
      n =>
        n.kind === 'condition'
        && extractTriggerIdsFromCondition(n.data).includes('keypad_event'),
    )
    const alarmoCond = doc.nodes.find(
      n =>
        n.kind === 'condition'
        && extractTriggerIdsFromCondition(n.data).includes('alarmo_state_change'),
    )
    expect(keypadCond).toBeDefined()
    expect(alarmoCond).toBeDefined()

    expect(
      doc.edges.some(
        e =>
          e.source === keypad!.id
          && e.target === keypadCond!.id
          && (e.edgeKind === 'flow' || e.edgeKind === undefined),
      ),
    ).toBe(true)
    expect(
      doc.edges.some(
        e =>
          e.source === alarmo!.id
          && e.target === alarmoCond!.id
          && (e.edgeKind === 'flow' || e.edgeKind === undefined),
      ),
    ).toBe(true)
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

  it('layouts blueprint input children without vertical overlap', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })
    const blueprint = doc.nodes.find(n => n.kind === 'blueprint')
    const inputs = doc.nodes.filter(n => n.kind === 'blueprint_input')
    const ordered = inputs
      .map(n => ({
        y: doc.layout[n.id]!.y,
        h: estimateNodeSize(n).height,
      }))
      .sort((a, b) => a.y - b.y)
    for (let i = 0; i < ordered.length - 1; i++) {
      expect(ordered[i]!.y + ordered[i]!.h).toBeLessThanOrEqual(ordered[i + 1]!.y)
    }
    const groupSize = blueprint?.data.groupSize as { height: number } | undefined
    expect(groupSize?.height).toBeGreaterThan(ordered[ordered.length - 1]!.y)
  })

  it('creates choose with conditions inside and only a Default option marker', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, { source: 'presence_based_lighting.yaml' })
    const chooseNode = doc.nodes.find(n => n.kind === 'choose')
    expect(chooseNode?.data.isContainer).toBe(true)
    const conditions = doc.nodes.filter(
      n => n.kind === 'condition' && n.parentId === chooseNode?.id,
    )
    expect(conditions.length).toBeGreaterThan(0)
    const optionMarkers = doc.nodes.filter(n => n.kind === 'choose_option')
    expect(optionMarkers.length).toBe(1)
    expect(optionMarkers[0]?.data.key).toBe('opt-default')
  })

  it('does not materialize sequence container nodes for inline action lists', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: false,
    })
    expect(doc.nodes.some(n => n.kind === 'sequence')).toBe(false)
    const chooseNode = doc.nodes.find(n => n.kind === 'choose')
    const turnOn = doc.nodes.find(
      n =>
        n.kind === 'action'
        && typeof n.data.service === 'string'
        && n.data.service.includes('turn_on'),
    )
    expect(turnOn).toBeDefined()
    expect(turnOn?.parentId).not.toBe(chooseNode?.id)
  })

  it('places branch actions outside the choose parent', () => {
    const yaml = loadBlueprint('blueprints/automations/presence_based_lighting.yaml')
    const doc = parseAutomationYaml(yaml, {
      source: 'presence_based_lighting.yaml',
      preview: false,
    })
    const chooseNode = doc.nodes.find(n => n.kind === 'choose')
    const turnOn = doc.nodes.find(
      n =>
        n.kind === 'action'
        && typeof n.data.service === 'string'
        && n.data.service.includes('turn_on'),
    )
    expect(turnOn).toBeDefined()
    expect(turnOn?.parentId).not.toBe(chooseNode?.id)
    const branchSources = doc.nodes.filter(
      n =>
        n.parentId === chooseNode?.id
        && (n.kind === 'condition' || n.kind === 'choose_option'),
    )
    const branchFlow = doc.edges.filter(
      e =>
        e.edgeKind === 'flow'
        && branchSources.some(s => s.id === e.source),
    )
    expect(branchFlow.length).toBeGreaterThan(0)
    expect(
      branchFlow.some(
        e => e.target === turnOn?.id || e.target === turnOn?.parentId,
      ),
    ).toBe(true)
    expect(
      doc.edges.some(
        e => e.edgeKind === 'flow' && e.source === chooseNode?.id,
      ),
    ).toBe(false)
  })
})
