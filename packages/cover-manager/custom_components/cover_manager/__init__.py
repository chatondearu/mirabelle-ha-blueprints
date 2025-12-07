"""The Cover Manager integration."""
import logging
import yaml
from pathlib import Path
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .templates.generate_cover_template import generate_cover_template, write_cover_template

_LOGGER = logging.getLogger(__name__)

DOMAIN = "cover_manager"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cover Manager from a config entry."""
    try:
        cover_id = entry.data['name'].lower().replace(' ', '_')
        position_helper_id = f"{cover_id}_position"
        direction_helper_id = f"{cover_id}_direction"
        
        # Create input_text helpers configuration
        helpers_config = {
            "input_text": {
                position_helper_id: {
                    "name": f"{entry.data['name']} Position",
                    "initial": "0",
                    "min": 0,
                    "max": 100,
                    "mode": "box"
                },
                direction_helper_id: {
                    "name": f"{entry.data['name']} Direction",
                    "initial": "stopped",
                    "mode": "text"
                }
            }
        }
        
        # Write helpers configuration to a package file
        packages_path = Path(hass.config.config_dir) / "configuration" / "packages"
        packages_path.mkdir(parents=True, exist_ok=True)
        helpers_path = packages_path / f"{DOMAIN}_{cover_id}_helpers.yaml"
        
        # Read existing helpers if file exists
        existing_helpers = {}
        if helpers_path.exists():
            try:
                with open(helpers_path, 'r') as f:
                    existing_config = yaml.safe_load(f) or {}
                    existing_helpers = existing_config.get("input_text", {})
            except Exception as e:
                _LOGGER.warning("Error reading existing helpers config: %s", e)
        
        # Merge with existing helpers
        if not existing_helpers:
            existing_helpers = helpers_config["input_text"]
        else:
            existing_helpers.update(helpers_config["input_text"])
        
        # Write merged configuration
        final_config = {"input_text": existing_helpers}
        with open(helpers_path, 'w') as f:
            yaml.dump(final_config, f, default_flow_style=False, sort_keys=False)
        
        # Reload input_text to load the new helpers
        await hass.services.async_call("input_text", "reload")
        
        # Create script if it doesn't exist
        script_path = Path(hass.config.config_dir) / "scripts" / "set_cover_position.yaml"
        if not script_path.exists():
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_source = Path(__file__).parent / "scripts" / "set_cover_position.yaml"
            if script_source.exists():
                with open(script_source, 'r') as f:
                    script_content = f.read()
                with open(script_path, 'w') as f:
                    f.write(script_content)
                # Reload scripts
                await hass.services.async_call("script", "reload")
        
        # Generate and write cover template
        config = generate_cover_template(
            cover_id=cover_id,
            name=entry.data['name'],
            switch_entity=entry.data['switch_entity'],
            travel_time=entry.data['travel_time']
        )
        
        covers_path = Path(hass.config.config_dir) / "configuration" / "covers.yaml"
        covers_path.parent.mkdir(parents=True, exist_ok=True)
        write_cover_template(config, str(covers_path))
        
        # Reload YAML configuration to load the new cover template
        # Note: This requires the covers.yaml to be included in configuration.yaml
        try:
            await hass.services.async_call("homeassistant", "reload_config_entry", {"entry_id": entry.entry_id})
        except Exception as reload_error:
            _LOGGER.warning("Could not reload config entry, trying full YAML reload: %s", reload_error)
            # Fallback: reload all YAML configurations
            # This will reload all YAML configurations including covers.yaml
            # Note: covers.yaml must be included in configuration.yaml for this to work
            try:
                await hass.services.async_call("homeassistant", "reload_all")
            except Exception as reload_all_error:
                _LOGGER.error("Could not reload YAML configurations: %s", reload_all_error)
                _LOGGER.warning("Cover template written but not loaded. Please restart Home Assistant or manually reload YAML configurations.")
        
        _LOGGER.info("Cover Manager setup completed for %s", entry.data['name'])
        return True
        
    except Exception as e:
        _LOGGER.error("Error setting up Cover Manager: %s", e, exc_info=True)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True 