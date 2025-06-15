# Scheduled Bell Sound

This blueprint allows you to play a sound at specific times with volume control and automatic restoration.

## Installation

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
- Volume restoration
- Flexible schedule configuration
- Custom audio file support

## Prerequisites

- A compatible media player (media_player)
- An audio file in the Home Assistant media_source folder

## Configuration

### Required Parameters

- **Media Player**: Select your media player
- **Sound File**: Path to the audio file (default: Japanese school bell sound)

### Optional Parameters

- **Announce Volume Level**: Volume level for the announcement (0-1, default: 0.5)
- **Volume Reduction**: Volume reduction for the announcement (0-1, default: 0.2)
- **Play Times**: Times to play the sound (24-hour format)
- **Use Sun Events**: Enable/disable sun events
- **Sun Event Offset**: Offset for sun events in minutes (-120 to +120)
- **Wait Time**: Time to wait before restoring volume (1-300 seconds)

## Usage Examples

### School Bell
```yaml
media_player: media_player.living_room_speaker
sound_file: media-source://media_source/local/section9/sounds/japan_school_bell.mp3
play_times:
  - "08:00:00"
  - "10:00:00"
  - "12:00:00"
  - "14:00:00"
  - "16:00:00"
use_sun_events: false
```

### Daily Reminder
```yaml
media_player: media_player.kitchen_speaker
sound_file: media-source://media_source/local/notifications/reminder.mp3
play_times:
  - "19:00:00"
use_sun_events: true
sun_offset: -30
```

### Prayer Time
```yaml
media_player: media_player.living_room_speaker
sound_file: media-source://media_source/local/religious/prayer_bell.mp3
play_times:
  - "06:00:00"
  - "12:00:00"
  - "18:00:00"
use_sun_events: true
sun_offset: 0
```

## Customization

1. **Times**: Configure exact play times
2. **Volume**: Adjust announcement volume and reduction
3. **Audio File**: Use any audio file from your library
4. **Sun Events**: Enable/disable sun-based triggers
5. **Wait Time**: Adjust time before volume restoration

## Troubleshooting

- Check if the media player is online
- Ensure the audio file exists in the specified path
- Check media_source folder permissions
- Adjust wait time if volume doesn't restore properly 