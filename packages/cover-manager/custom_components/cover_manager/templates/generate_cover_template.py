"""Generate cover template configuration."""
import yaml
import os
from pathlib import Path
from typing import Dict, Any

def generate_cover_template(cover_id: str, name: str, switch_entity: str, travel_time: int) -> dict:
    """Generate cover template configuration for a single cover."""
    return {
        cover_id: {
            "friendly_name": name,
            "unique_id": f"{cover_id}_template",
            "value_template": "{{ states(position_helper) | int }}",
            "open_cover": {
                "service": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": 100,
                    "travel_time": travel_time,
                    "last_state": "{{ position_helper }}"
                }
            },
            "close_cover": {
                "service": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": 0,
                    "travel_time": travel_time,
                    "last_state": "{{ position_helper }}"
                }
            },
            "stop_cover": {
                "service": "switch.turn_off",
                "target": {
                    "entity_id": switch_entity
                }
            },
            "set_cover_position": {
                "service": "script.set_cover_position",
                "data": {
                    "cover_switch": switch_entity,
                    "position": "{{ position }}",
                    "travel_time": travel_time,
                    "last_state": "{{ position_helper }}"
                }
            },
            "icon_template": "{% if is_state(switch_entity, 'on') %}{% if states(direction_helper) == 'opening' %}mdi:arrow-up-bold{% else %}mdi:arrow-down-bold{% endif %}{% else %}{% if states(position_helper) | int == 0 %}mdi:window-closed{% elif states(position_helper) | int == 100 %}mdi:window-open{% else %}mdi:window-shutter{% endif %}{% endif %}"
        }
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

if __name__ == "__main__":
    # Example usage
    config = generate_cover_template(
        cover_id="living_room_blind",
        name="Living Room Blind",
        switch_entity="switch.living_room_blind",
        travel_time=30
    )
    write_cover_template(config, "cover_template.yaml") 