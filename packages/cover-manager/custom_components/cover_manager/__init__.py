"""The Cover Manager integration."""
import logging
import yaml
from pathlib import Path
from functools import partial
import re
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .templates.generate_cover_template import (
    generate_cover_template,
    write_single_cover_template,
)
from .const import DEFAULT_HELPERS_PATH, DEFAULT_TEMPLATE_COVERS_PATH, DOMAIN

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

        async def _extract_include_path(section: str, default_path: str, merge_type: str) -> str:
            """Best-effort extraction of include dir from configuration.yaml for a section."""
            config_yaml = Path(hass.config.path("configuration.yaml"))
            if not config_yaml.exists():
                return default_path
            try:
                content = await hass.async_add_executor_job(config_yaml.read_text)
            except Exception:
                return default_path
            lines = content.splitlines()
            inside_section = False
            include_pattern = rf"!include_dir_merge_{merge_type}\\s+([^\\s]+)"
            section_header = rf"^{section}:\\s*(?:!include_dir_merge_{merge_type}\\s+[^\\s]+)?"
            for line in lines:
                stripped = line.strip()
                if re.match(section_header, stripped):
                    inside_section = True
                elif re.match(r"^\\S", stripped) and inside_section:
                    inside_section = False
                if inside_section:
                    match = re.search(include_pattern, stripped)
                    if match:
                        return match.group(1)
            return default_path

        async def _warn_include_config(path_to_check: Path, merge_type: str, section: str) -> None:
            """Warn user if configuration.yaml does not include the given folder for the section."""
            config_yaml = Path(hass.config.path("configuration.yaml"))
            if not config_yaml.exists():
                _LOGGER.warning(
                    "configuration.yaml not found; ensure you include your %s folder manually (e.g. %s: !include_dir_merge_%s %s)",
                    section,
                    section,
                    merge_type,
                    path_to_check.relative_to(Path(hass.config.config_dir)),
                )
                return
            try:
                content = await hass.async_add_executor_job(config_yaml.read_text)
            except Exception as err:
                _LOGGER.warning(
                    "Could not read configuration.yaml to verify %s include: %s",
                    section,
                    err,
                )
                return
            rel = path_to_check.relative_to(Path(hass.config.config_dir))
            snippet = f"!include_dir_merge_{merge_type} {rel}"
            if section + ":" not in content or snippet not in content:
                _LOGGER.warning(
                    "%s include for %s not detected in configuration.yaml. Add:\n"
                    "%s:\n  - !include_dir_merge_%s %s",
                    section.capitalize(),
                    rel,
                    section,
                    merge_type,
                    rel,
                )

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
        
        # Try to read includes from configuration.yaml; fallback to defaults
        helpers_base = await _extract_include_path("input_text", DEFAULT_HELPERS_PATH, "named")
        packages_path = _safe_path(helpers_base, DEFAULT_HELPERS_PATH, "helpers_path")
        packages_path.mkdir(parents=True, exist_ok=True)
        helpers_path = packages_path / f"{DOMAIN}_{cover_id}_helpers.yaml"
        
        # Read and merge helpers (offload to executor)
        def _write_helpers():
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
                # Only update if helper doesn't exist or is different
                for key, value in helpers_config["input_text"].items():
                    if key not in existing_helpers:
                        existing_helpers[key] = value
            
            # Write merged configuration
            final_config = {"input_text": existing_helpers}
            with open(helpers_path, 'w') as f:
                yaml.dump(final_config, f, default_flow_style=False, sort_keys=False)
        
        await hass.async_add_executor_job(_write_helpers)
        
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
        
        covers_rel_path = await _extract_include_path("template", DEFAULT_TEMPLATE_COVERS_PATH, "list")
        covers_base = _safe_path(covers_rel_path, DEFAULT_TEMPLATE_COVERS_PATH, "covers_path")
        covers_base.mkdir(parents=True, exist_ok=True)
        cover_file = covers_base / f"cover_manager_{cover_id}.yaml"
        await _warn_include_config(covers_base, "list", "template")
        
        # Check if file already exists to avoid rewriting unnecessarily
        file_exists = await hass.async_add_executor_job(cover_file.exists)
        
        # Offload YAML write to executor to avoid blocking event loop
        await hass.async_add_executor_job(
            partial(write_single_cover_template, config, str(cover_file))
        )
        
        # Only reload YAML if this is a new file or if we need to refresh
        # Avoid reloading the config entry itself to prevent loops
        if not file_exists:
            _LOGGER.info("New cover template created: %s", cover_file)
            # Reload YAML configurations to load the new cover template
            # Note: This requires the covers directory to be included in configuration.yaml
            try:
                await hass.services.async_call("homeassistant", "reload_all")
                _LOGGER.info("YAML configurations reloaded to load new cover template")
            except Exception as reload_error:
                _LOGGER.warning(
                    "Could not reload YAML configurations: %s. "
                    "Please restart Home Assistant or manually reload YAML configurations.",
                    reload_error
                )
        else:
            _LOGGER.debug("Cover template already exists, skipping reload to avoid loops")
        
        _LOGGER.info("Cover Manager setup completed for %s", entry.data['name'])
        return True
        
    except Exception as e:
        _LOGGER.error("Error setting up Cover Manager: %s", e, exc_info=True)
        return False


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Basic setup; paths are fixed and managed via HA includes."""
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True 