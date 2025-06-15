# Play Sound with Volume Control

This script allows you to play a sound with automatic volume control and restoration.

## Features

- Play sound on a media player
- Automatic volume control
- Volume restoration
- Announcement support
- Configurable wait time

## Prerequisites

- A compatible media player (media_player)
- An audio file in the Home Assistant media_source folder

## Configuration

### Required Parameters

- **Media Player**: Select your media player
- **Sound File**: Path to the audio file

### Optional Parameters

- **Announce Volume Level**: Volume level for the announcement (0-1, default: 0.5)
- **Volume Reduction**: Volume reduction for the announcement (0-1, default: 0.2)
- **Wait Time**: Time to wait before restoring volume (1-300 seconds)

## Usage Examples

### Simple Playback
```yaml
service: script.play_sound_with_volume_control
data:
  media_player: media_player.living_room_speaker
  sound_file: media-source://media_source/local/notifications/notification.mp3
```

### Custom Volume Playback
```yaml
service: script.play_sound_with_volume_control
data:
  media_player: media_player.kitchen_speaker
  sound_file: media-source://media_source/local/alarms/alarm.mp3
  announce_volume: 0.7
  volume_reduction: 0.3
  wait_time: 30
```

### Integration in Automation
```yaml
automation:
  trigger:
    - platform: time
      at: "08:00:00"
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/music/wake_up.mp3
        announce_volume: 0.6
        volume_reduction: 0.2
        wait_time: 20
```

## Customization

1. **Volume**: Adjust announcement volume and reduction
2. **Audio File**: Use any audio file from your library
3. **Wait Time**: Adjust time before volume restoration

## Troubleshooting

- Check if the media player is online
- Ensure the audio file exists in the specified path
- Adjust wait time if volume doesn't restore properly
- Check media_source folder permissions

## Usage with Other Blueprints

This script can be used in any automation or other script. It's particularly useful for:
- Sound notifications
- Alarms
- Reminders
- Announcements
- Sound effects 