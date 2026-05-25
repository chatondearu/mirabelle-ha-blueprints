import { describe, expect, it } from 'vitest'
import { summarizeCondition, summarizeServiceAction } from './action-expander.js'

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
