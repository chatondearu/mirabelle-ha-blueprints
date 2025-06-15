# [CDA] 🔔 Scheduled Bell Sound

This blueprint allows you to play a bell sound at specific times and during solar events.

## Installation

1. Click on the following link to open the blueprint import dialog in your Home Assistant instance:
[Import Scheduled Bell Sound Blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fscheduled_bell_sound.yaml)

Alternatively, you can manually import the blueprint:
1. Go to your Home Assistant instance
2. Click on "Blueprints" in the sidebar
3. Click on the "+" button in the bottom right corner
4. Click on "Import Blueprint"
5. Paste the following URL:
```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/scheduled_bell_sound.yaml
```

## Features

- Play sound at specific times
- Support for multiple trigger types:
  - Time-based triggers
  - Sun events (sunrise/sunset)
  - State changes
  - Custom events
  - MQTT messages
  - Webhooks
- Automatic volume control
- Flexible schedule management

## Prerequisites

- A compatible media player (media_player)
- An audio file in the Home Assistant media_source folder
- The `play_sound_with_volume_control` script installed

## Configuration

### Required Parameters

- **Media Player**: Select your media player
- **Sound File**: Path to the audio file
- **Triggers**: At least one trigger configuration

### Optional Parameters

- **Announce Volume Level**: Volume level for the announcement (0-1, default: 0.5)
- **Volume Reduction**: Volume reduction for the announcement (0-1, default: 0.2)
- **Wait Time**: Time to wait before restoring volume (1-300 seconds, default: 20)

### Trigger Configuration

The blueprint now supports multiple trigger types that can be combined:

#### Time Trigger
```yaml
platform: time
at: "08:00:00"
```

#### Sun Event Trigger
```yaml
platform: sun
event: sunrise
offset: "-00:30:00"  # 30 minutes before sunrise
```

#### State Trigger
```yaml
platform: state
entity_id: input_boolean.schedule
from: "off"
to: "on"
```

#### Event Trigger
```yaml
platform: event
event_type: custom_event
```

#### MQTT Trigger
```yaml
platform: mqtt
topic: "home/bell/trigger"
payload: "ring"
```

## Usage Examples

### School Bell with Multiple Triggers
```yaml
automation:
  trigger:
    - platform: time
      at: "08:00:00"
    - platform: time
      at: "09:45:00"
    - platform: sun
      event: sunset
      offset: "-00:30:00"
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/sounds/school_bell.mp3
        announce_volume: 0.5
        volume_reduction: 0.2
        wait_time: 20
```

### Prayer Time with Sun Events
```yaml
automation:
  trigger:
    - platform: sun
      event: sunrise
      offset: "-00:30:00"
    - platform: sun
      event: sunset
      offset: "00:30:00"
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/sounds/prayer.mp3
        announce_volume: 0.6
        volume_reduction: 0.3
        wait_time: 30
```

## Customization

1. **Triggers**: Configure any combination of supported trigger types
2. **Volume**: Adjust announcement volume and reduction
3. **Audio File**: Use any audio file from your library
4. **Wait Time**: Adjust time before volume restoration

## Troubleshooting

- Check if the media player is online
- Ensure the audio file exists in the specified path
- Verify trigger configurations
- Check if the `play_sound_with_volume_control` script is installed
- Adjust wait time if volume doesn't restore properly
- Check media_source folder permissions

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Licence

Ce blueprint est distribué sous la licence MIT. 