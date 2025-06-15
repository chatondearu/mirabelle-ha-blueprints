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
- Support for sun events (sunrise/sunset)
- Automatic volume control
- Custom triggers support
- Flexible schedule management

## Prerequisites

- A compatible media player (media_player)
- An audio file in the Home Assistant media_source folder
- Optional: Binary sensors for custom triggers

## Configuration

### Required Parameters

- **Media Player**: Select your media player
- **Sound File**: Path to the audio file

### Optional Parameters

- **Use Time Triggers**: Enable/disable time-based triggers
- **Play Times**: Times to play the sound (24-hour format)
- **Use Sun Events**: Enable/disable sun-based triggers
- **Sun Event Offset**: Offset for sun events in minutes
- **Announce Volume Level**: Volume level for the announcement (0-1)
- **Volume Reduction**: Volume reduction for the announcement (0-1)
- **Wait Time**: Time to wait before restoring volume (1-300 seconds)
- **Custom Triggers**: Additional binary sensors to trigger the sound

## Creating a Schedule

To easily create a schedule, you can use the "Create Schedule" script:

1. Import the script blueprint:
[Import Create Schedule Script](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate_schedule.yaml)

2. Create a new script using this blueprint
3. Configure the schedule name and times
4. Run the script to create the schedule
5. Use the created schedule in the Scheduled Bell Sound blueprint

## Usage Examples

### School Bell
```yaml
automation:
  trigger:
    - platform: time
      at: 
        - "08:00:00"
        - "09:45:00"
        - "10:00:00"
        - "11:45:00"
        - "13:30:00"
        - "15:15:00"
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/sounds/school_bell.mp3
```

### Daily Reminder with Custom Trigger
```yaml
automation:
  trigger:
    - platform: time
      at: "12:00:00"
    - platform: state
      entity_id: binary_sensor.door_sensor
      to: "on"
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.kitchen_speaker
        sound_file: media-source://media_source/local/sounds/reminder.mp3
```

### Prayer Time with Sun Events
```yaml
automation:
  trigger:
    - platform: sun
      event: sunrise
      offset: -30
    - platform: sun
      event: sunset
      offset: 30
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/sounds/prayer.mp3
```

## Customization

1. **Time Triggers**: Enable/disable time-based triggers
2. **Sun Events**: Configure sunrise/sunset triggers
3. **Custom Triggers**: Add binary sensors as triggers
4. **Volume**: Adjust announcement volume and reduction
5. **Audio File**: Use any audio file from your library
6. **Wait Time**: Adjust time before volume restoration

## Troubleshooting

- Check if the media player is online
- Ensure the audio file exists in the specified path
- Verify trigger configurations
- Check custom trigger states
- Adjust wait time if volume doesn't restore properly
- Check media_source folder permissions 