/** Mock blueprint inputs mirroring tests/fixtures/blueprint_inputs.py */
export const BLUEPRINT_INPUT_FIXTURES: Record<string, Record<string, unknown>> = {
  'presence_based_lighting.yaml': {
    presence_sensor: 'binary_sensor.test_motion',
    light_entity: 'light.test',
    delay_off: 5,
  },
  'create_schedule.yaml': {
    schedule_name: 'input_datetime.test_schedule',
    times: ['08:00:00', '12:00:00'],
  },
  'cover_control.yaml': {
    cover_name: 'Test Cover',
    cover_switch: 'switch.test_cover',
    travel_time: 5,
    position: 50,
  },
}
