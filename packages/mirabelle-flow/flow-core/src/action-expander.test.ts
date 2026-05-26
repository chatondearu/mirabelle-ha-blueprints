import { describe, expect, it } from 'vitest'
import {
  parseIfActionShape,
  summarizeCondition,
  summarizeServiceAction,
} from './action-expander.js'

describe('parseIfActionShape', () => {
  it('detects if/then/else with a condition list under if', () => {
    const shape = parseIfActionShape({
      if: [{ condition: 'template', value_template: '{{ true }}' }],
      then: [{ service: 'light.turn_on' }],
      else: [{ service: 'light.turn_off' }],
    })
    expect(shape.mode).toBe('then_else')
    expect(shape.conditions).toHaveLength(1)
    expect(shape.thenSeq).toHaveLength(1)
    expect(shape.elseSeq).toHaveLength(1)
  })

  it('detects legacy if branch list with sequence per branch', () => {
    const shape = parseIfActionShape({
      if: [
        {
          conditions: [{ condition: 'state', entity_id: 'light.x', state: 'on' }],
          sequence: [{ service: 'light.turn_on' }],
        },
      ],
      else: [{ service: 'light.turn_off' }],
    })
    expect(shape.mode).toBe('branches')
    expect(shape.branches).toHaveLength(1)
    expect(shape.elseSeq).toHaveLength(1)
  })
})

describe('action-expander summaries', () => {
  it('summarizes template conditions', () => {
    const label = summarizeCondition({
      condition: 'template',
      value_template: "{{ trigger.to_state.state == 'on' }}",
    })
    expect(label).toContain('Template:')
    expect(label).toContain('trigger')
  })

  it('summarizes service actions with target and data keys', () => {
    const label = summarizeServiceAction({
      service: 'light.turn_on',
      target: { entity_id: 'light.kitchen' },
      data: { brightness_pct: 80 },
    })
    expect(label).toContain('light.turn_on')
    expect(label).toContain('light.kitchen')
    expect(label).toContain('brightness_pct')
  })
})
