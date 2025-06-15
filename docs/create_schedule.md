# Create Schedule

This script helps you create a schedule for your automations by managing input_datetime entities.

## Installation

1. Click on the following link to open the blueprint import dialog in your Home Assistant instance:
[Import Create Schedule Script](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate_schedule.yaml)

Alternatively, you can manually import the blueprint:
1. Go to your Home Assistant instance
2. Click on "Blueprints" in the sidebar
3. Click on the "+" button in the bottom right corner
4. Click on "Import Blueprint"
5. Paste the following URL:
```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/create_schedule.yaml
```

## Features

- Create a schedule with multiple times
- Easy to use in automations
- Flexible time format
- Multiple schedules support

## Configuration

### Required Parameters

- **Schedule Name**: Name of the schedule (will be used as the input_datetime entity_id)
- **Times**: List of times in 24-hour format (HH:MM:SS)

## Usage Examples

### Basic Schedule
```yaml
script:
  alias: "Create Basic Schedule"
  sequence:
    - service: script.create_schedule
      data:
        schedule_name: "morning_schedule"
        times:
          - "06:00:00"
          - "07:00:00"
          - "08:00:00"
```

### School Schedule
```yaml
script:
  alias: "Create School Schedule"
  sequence:
    - service: script.create_schedule
      data:
        schedule_name: "school_bell"
        times:
          - "08:00:00"
          - "09:45:00"
          - "10:00:00"
          - "11:45:00"
          - "13:30:00"
          - "15:15:00"
```

### Using the Schedule in an Automation
```yaml
automation:
  trigger:
    - platform: time
      at: !input school_bell
  action:
    - service: script.play_sound_with_volume_control
      data:
        media_player: media_player.living_room_speaker
        sound_file: media-source://media_source/local/sounds/school_bell.mp3
```

## Customization

1. **Schedule Name**: Choose a descriptive name for your schedule
2. **Times**: Add or remove times as needed
3. **Time Format**: Use 24-hour format (HH:MM:SS)

## Troubleshooting

- Check if the input_datetime entity was created
- Verify the times are in the correct format
- Make sure the schedule name is unique
- Check the script execution logs

## Integration with Other Blueprints

This script works well with:
- Scheduled Bell Sound blueprint
- Any automation that needs time-based triggers
- Custom automations using input_datetime 