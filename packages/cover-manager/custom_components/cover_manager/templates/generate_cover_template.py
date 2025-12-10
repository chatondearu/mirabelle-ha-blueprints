"""Generate cover template configuration."""
import yaml
import os
from pathlib import Path
from typing import Dict, Any

def generate_cover_template(cover_id: str, name: str, switch_entity: str, travel_time: int) -> dict:
    """Generate cover template configuration for a single cover using modern template syntax.
    
    Uses the new template: - cover: syntax instead of deprecated cover: platform: template.
    """
    # Use full entity IDs for helpers
    position_helper = f"input_text.{cover_id}_position"
    direction_helper = f"input_text.{cover_id}_direction"
    entity_id = f"cover.{cover_id}"
    
    return {
        "unique_id": f"{cover_id}_template",
        "name": name,
        "default_entity_id": entity_id,
        # Use default(0) to handle 'unknown' state when helper is not loaded yet
        "state": f"{{{{ states('{position_helper}') | default('0') | int }}}}",
        "open_cover": [
            {
                "action": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": 100,
                    "travel_time": travel_time,
                    "last_state": position_helper
                }
            }
        ],
        "close_cover": [
            {
                "action": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": 0,
                    "travel_time": travel_time,
                    "last_state": position_helper
                }
            }
        ],
        "stop_cover": [
            {
                "action": "switch.turn_off",
                "target": {
                    "entity_id": [switch_entity]
                }
            }
        ],
        "set_cover_position": [
            {
                "action": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": "{{ position }}",
                    "travel_time": travel_time,
                    "last_state": position_helper
                }
            }
        ],
        # Use default() to handle 'unknown' state in icon template
        "icon": (
            f"{{% if is_state('{switch_entity}', 'on') %}}"
            f"{{% if states('{direction_helper}') | default('stopped') == 'opening' %}}mdi:arrow-up-bold"
            f"{{% else %}}mdi:arrow-down-bold{{% endif %}}"
            f"{{% else %}}"
            f"{{% set pos = states('{position_helper}') | default('0') | int %}}"
            f"{{% if pos == 0 %}}mdi:window-closed"
            f"{{% elif pos == 100 %}}mdi:window-open"
            f"{{% else %}}mdi:window-shutter{{% endif %}}"
            f"{{% endif %}}"
        )
    }

def read_existing_config(config_path: str) -> Dict[str, Any]:
    """Read existing cover configuration if it exists."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {"cover": [{"platform": "template", "covers": {}}]}
    return {"cover": [{"platform": "template", "covers": {}}]}

def write_cover_template(config: dict, output_path: str) -> None:
    """Write cover template configuration to file."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Read existing configuration
    existing_config = read_existing_config(output_path)
    
    # Update the covers section with the new cover
    if "cover" in existing_config and len(existing_config["cover"]) > 0:
        if "covers" not in existing_config["cover"][0]:
            existing_config["cover"][0]["covers"] = {}
        existing_config["cover"][0]["covers"].update(config)
    else:
        existing_config = {
            "cover": [
                {
                    "platform": "template",
                    "covers": config
                }
            ]
        }
    
    # Write the updated configuration
    with open(output_path, 'w') as f:
        yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)


def write_single_cover_template(config: dict, output_path: str) -> None:
    """Write a single cover template configuration to its own file.
    
    This creates a file compatible with !include_dir_merge_list using the modern
    template: - cover: syntax (replacing deprecated cover: platform: template).
    
    Each file contains directly a list item that will be merged into the
    template: - cover: list in configuration.yaml.
    
    Example structure in the generated file:
    - cover:
      - unique_id: ...
        name: ...
        state: ...
        ...
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Structure for !include_dir_merge_list: each file contains directly a list item
    # The 'template:' key is in configuration.yaml, not in individual files
    # Each file contains: - cover: [config]
    single_config = [
        {
            "cover": [config]
        }
    ]
    with open(output_path, 'w') as f:
        yaml.dump(single_config, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    # Example usage
    config = generate_cover_template(
        cover_id="living_room_blind",
        name="Living Room Blind",
        switch_entity="switch.living_room_blind",
        travel_time=30
    )
    write_cover_template(config, "cover_template.yaml") 