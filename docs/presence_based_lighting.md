# Presence-Based Lighting Automation

This blueprint allows you to automatically control lights based on presence detection.

## Installation

1. Go to your Home Assistant instance
2. Click on "Blueprints" in the sidebar
3. Click on the "+" button in the bottom right corner
4. Click on "Import Blueprint"
5. Paste the following URL:
```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/presence_based_lighting.yaml
```

## Features

- Automatic light control based on presence
- Support for multiple presence sensors
- Configurable light groups
- Time-based conditions
- Brightness control
- Color temperature control

## Prerequisites

- Presence sensors (motion, presence, or zone sensors)
- Controllable lights
- Optional: Light groups

## Configuration

### Required Parameters

- **Presence Sensors**: Select one or more presence sensors
- **Lights**: Select the lights to control
- **Light Groups**: Optional light groups for coordinated control

### Optional Parameters

- **Time Conditions**: Set time windows for automation
- **Brightness Level**: Set desired brightness (0-255)
- **Color Temperature**: Set color temperature in Kelvin
- **Transition Time**: Set light transition duration

## Usage Examples

### Basic Presence Detection
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.living_room_motion
      to: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness: 255
        kelvin: 2700
```

### Multiple Sensors
```yaml
automation:
  trigger:
    - platform: state
      entity_id: 
        - binary_sensor.living_room_motion
        - binary_sensor.kitchen_motion
      to: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: 
          - light.living_room
          - light.kitchen
      data:
        brightness: 200
        kelvin: 3000
```

### Time-Based Control
```yaml
automation:
  trigger:
    - platform: state
      entity_id: binary_sensor.living_room_motion
      to: "on"
  condition:
    - condition: time
      after: "17:00:00"
      before: "23:00:00"
  action:
    - service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness: 150
        kelvin: 2200
```

## Customization

1. **Sensors**: Add or remove presence sensors
2. **Lights**: Configure individual or group control
3. **Timing**: Set specific time windows
4. **Light Settings**: Adjust brightness and color temperature

## Troubleshooting

- Check sensor status and battery levels
- Verify light connectivity
- Test sensor coverage
- Check automation triggers
- Verify time conditions

## Integration with Other Blueprints

This blueprint can be combined with:
- Time-based automations
- Scene controllers
- Energy management
- Security systems 