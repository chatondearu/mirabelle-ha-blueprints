# Living Area Lighting Hub

Publishes a shared `morning` / `day` / `evening` / `night` profile to an
`input_select`. Room [Living Area Adaptive Lighting](living-area-adaptive-lighting.md)
automations can follow this mode when **Follow Global Profile Hub** is enabled.

The hub never turns lights on or off.

## Installation

1. Ensure `shell_command.cda_write_living_area_lighting_helper_package` exists (same as LAL helpers).
2. Import and run **[CDA] Create LAL Hub Helpers** once.
3. Import the hub automation blueprint and create one automation instance.

[Import Living Area Lighting Hub](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fliving-area-lighting-hub.yaml)

[Import Create LAL Hub Helpers](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate-lal-hub-helpers.yaml)

## Configuration

Match the schedule inputs to your preferred global night/evening/morning windows
(same model as LAL profile schedule). Point **Global Profile Helper** at
`input_select.cda_lal_global_profile` (default).

On each room LAL automation, enable **Follow Global Profile Hub** when you want
that room to use the hub mode while its local mode helper is `auto`.

## Changelog

### 1.0.0

- Initial hub: shared profile schedule → `input_select`.
