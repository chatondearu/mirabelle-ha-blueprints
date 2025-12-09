"""The Cover Manager integration."""
import logging
import yaml
from pathlib import Path
from functools import partial
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .templates.generate_cover_template import (
    generate_cover_template,
    write_single_cover_template,
)
from .const import DEFAULT_HELPERS_PATH, DEFAULT_COVERS_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cover Manager from a config entry."""
    try:
        cover_id = entry.data['name'].lower().replace(' ', '_')
        position_helper_id = f"{cover_id}_position"
        direction_helper_id = f"{cover_id}_direction"
        
        # Create input_text helpers configuration
        def _safe_path(base_path: str, default_path: str, label: str) -> Path:
            """Ensure path stays inside HA config dir; fallback if not."""
            config_dir = Path(hass.config.config_dir).resolve()
            candidate = (config_dir / base_path).resolve()
            if not str(candidate).startswith(str(config_dir)):
                _LOGGER.warning(
                    "Invalid %s path '%s' (outside config dir), falling back to '%s'",
                    label,
                    candidate,
                    default_path,
                )
                candidate = (config_dir / default_path).resolve()
            return candidate

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
        yaml_overrides = hass.data.get(DOMAIN, {})
        helpers_base = yaml_overrides.get("helpers_path", DEFAULT_HELPERS_PATH)
        packages_path = _safe_path(helpers_base, DEFAULT_HELPERS_PATH, "helpers_path")
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
                # Offload file IO to executor to avoid blocking event loop
                script_content = await hass.async_add_executor_job(script_source.read_text)
                await hass.async_add_executor_job(script_path.write_text, script_content)
                # Reload scripts
                await hass.services.async_call("script", "reload")
        
        # Generate and write cover template
        config = generate_cover_template(
            cover_id=cover_id,
            name=entry.data['name'],
            switch_entity=entry.data['switch_entity'],
            travel_time=entry.data['travel_time']
        )
        
        covers_rel_path = yaml_overrides.get("covers_path", DEFAULT_COVERS_PATH)
        covers_base = _safe_path(covers_rel_path, DEFAULT_COVERS_PATH, "covers_path")
        covers_base.mkdir(parents=True, exist_ok=True)
        cover_file = covers_base / f"custom_cover_{cover_id}.yaml"
        # Offload YAML write to executor to avoid blocking event loop
        await hass.async_add_executor_job(
            partial(write_single_cover_template, config, str(cover_file))
        )
        
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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up from configuration.yaml to get default paths."""
    domain_cfg = config.get(DOMAIN, {}) or {}
    hass.data.setdefault(DOMAIN, {})
    if "helpers_path" in domain_cfg:
        hass.data[DOMAIN]["helpers_path"] = domain_cfg["helpers_path"]
    if "covers_path" in domain_cfg:
        hass.data[DOMAIN]["covers_path"] = domain_cfg["covers_path"]
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True 