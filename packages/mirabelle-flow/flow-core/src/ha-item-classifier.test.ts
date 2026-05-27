import { describe, expect, it } from 'vitest'
import { classifyHaItem, isHaConditionItem, isHaTriggerItem } from './ha-item-classifier.js'

describe('classifyHaItem', () => {
  it('detects conditions by `condition` field', () => {
    expect(
      classifyHaItem({
        condition: 'template',
        value_template: '{{ true }}',
      }),
    ).toBe('condition')
    expect(isHaConditionItem({ condition: 'state', entity_id: 'x' })).toBe(true)
  })

  it('detects triggers by platform', () => {
    expect(
      classifyHaItem({
        platform: 'state',
        entity_id: 'binary_sensor.motion',
      }),
    ).toBe('trigger')
    expect(isHaTriggerItem({ platform: 'time' })).toBe(true)
  })

  it('does not treat wait_for_trigger as a trigger item', () => {
    expect(classifyHaItem({ wait_for_trigger: [] })).toBe('wait')
  })

  it('detects service actions', () => {
    expect(classifyHaItem({ service: 'light.turn_on' })).toBe('service')
  })

  it('prefers condition over default action when only condition keys are set', () => {
    expect(
      classifyHaItem({
        condition: 'numeric_state',
        entity_id: 'sensor.x',
        below: 10,
      }),
    ).toBe('condition')
  })
})
