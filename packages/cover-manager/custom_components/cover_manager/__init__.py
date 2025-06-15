"""The Cover Manager integration."""
import os
import yaml
from pathlib import Path
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from .templates.generate_cover_template import generate_cover_template, write_cover_template

DOMAIN = "cover_manager"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cover Manager from a config entry."""
    # Get the entity registry
    entity_registry = er.async_get(hass)
    
    # Create input_text helpers if they don't exist
    position_helper = f"input_text.{entry.data['name'].lower().replace(' ', '_')}_position"
    direction_helper = f"input_text.{entry.data['name'].lower().replace(' ', '_')}_direction"
    
    # Check if helpers exist
    if not entity_registry.async_get(position_helper):
        # Create position helper
        entity_registry.async_get_or_create(
            "input_text",
            DOMAIN,
            f"{entry.data['name'].lower().replace(' ', '_')}_position",
            suggested_object_id=f"{entry.data['name'].lower().replace(' ', '_')}_position",
            name=f"{entry.data['name']} Position",
            initial_value="0",
            min_value=0,
            max_value=100,
            mode="box"
        )
    
    if not entity_registry.async_get(direction_helper):
        # Create direction helper
        entity_registry.async_get_or_create(
            "input_text",
            DOMAIN,
            f"{entry.data['name'].lower().replace(' ', '_')}_direction",
            suggested_object_id=f"{entry.data['name'].lower().replace(' ', '_')}_direction",
            name=f"{entry.data['name']} Direction",
            initial_value="stopped",
            mode="text"
        )
    
    # Create script if it doesn't exist
    script_path = Path(hass.config.config_dir) / "scripts" / "set_cover_position.yaml"
    if not script_path.exists():
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(Path(__file__).parent / "scripts" / "set_cover_position.yaml", "r") as f:
            script_content = f.read()
        with open(script_path, "w") as f:
            f.write(script_content)
    
    # Generate and write cover template
    cover_id = entry.data['name'].lower().replace(' ', '_')
    config = generate_cover_template(
        cover_id=cover_id,
        name=entry.data['name'],
        switch_entity=entry.data['switch_entity'],
        travel_time=entry.data['travel_time']
    )
    
    covers_path = Path(hass.config.config_dir) / "configuration" / "covers.yaml"
    covers_path.parent.mkdir(parents=True, exist_ok=True)
    write_cover_template(config, str(covers_path))
    
    # Reload configuration
    await hass.services.async_call("homeassistant", "reload_config_entry", {"entry_id": entry.entry_id})
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True 