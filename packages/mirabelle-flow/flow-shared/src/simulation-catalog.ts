import type { BlueprintInputDef, SimulationCatalog } from './types.js'

export const SIMULATION_CATALOG_STORAGE_KEY = 'mirabelle-flow-simulation-catalog'

export const DEFAULT_SIMULATION_CATALOG: SimulationCatalog = {
  lights: ['light.living_room', 'light.bedroom', 'light.test'],
  sensors: ['binary_sensor.motion', 'binary_sensor.test_motion'],
  switches: ['switch.test_cover'],
  media_players: ['media_player.living_room'],
  alarm_control_panels: ['alarm_control_panel.alarmo'],
  defaults: {},
}

export function loadSimulationCatalog(): SimulationCatalog {
  if (typeof localStorage === 'undefined') {
    return { ...DEFAULT_SIMULATION_CATALOG, defaults: { ...DEFAULT_SIMULATION_CATALOG.defaults } }
  }
  try {
    const raw = localStorage.getItem(SIMULATION_CATALOG_STORAGE_KEY)
    if (!raw) {
      return { ...DEFAULT_SIMULATION_CATALOG, defaults: { ...DEFAULT_SIMULATION_CATALOG.defaults } }
    }
    const parsed = JSON.parse(raw) as SimulationCatalog
    return {
      ...DEFAULT_SIMULATION_CATALOG,
      ...parsed,
      defaults: { ...DEFAULT_SIMULATION_CATALOG.defaults, ...parsed.defaults },
    }
  }
  catch {
    return { ...DEFAULT_SIMULATION_CATALOG, defaults: { ...DEFAULT_SIMULATION_CATALOG.defaults } }
  }
}

export function saveSimulationCatalog(catalog: SimulationCatalog): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.setItem(SIMULATION_CATALOG_STORAGE_KEY, JSON.stringify(catalog))
}

/** Pick a default simulation value for a blueprint input from catalog + HA-style selector. */
export function defaultSimulationValueForInput(
  input: BlueprintInputDef,
  catalog: SimulationCatalog,
): unknown {
  if (input.default !== undefined && input.default !== '') {
    return input.default
  }
  const selector = input.selector as Record<string, unknown> | undefined
  const entity = selector?.entity as { filter?: { domain?: string }[] } | undefined
  const filters = entity?.filter
  const domain = Array.isArray(filters)
    ? filters.find(f => f?.domain)?.domain
    : undefined

  if (domain === 'light' && catalog.lights[0]) {
    return catalog.lights[0]
  }
  if (domain === 'binary_sensor' && catalog.sensors[0]) {
    return catalog.sensors[0]
  }
  if (domain === 'switch' && catalog.switches[0]) {
    return catalog.switches[0]
  }
  if (domain === 'media_player' && catalog.media_players[0]) {
    return catalog.media_players[0]
  }
  if (domain === 'alarm_control_panel' && catalog.alarm_control_panels[0]) {
    return catalog.alarm_control_panels[0]
  }
  if (catalog.defaults[input.key]) {
    return catalog.defaults[input.key]
  }
  if (selector?.number) {
    return 0
  }
  if (selector?.boolean) {
    return false
  }
  return ''
}

export function buildSimulationValues(
  inputs: BlueprintInputDef[],
  catalog: SimulationCatalog,
  fixtureOverrides: Record<string, unknown> = {},
): Record<string, unknown> {
  const values: Record<string, unknown> = {}
  for (const input of inputs) {
    values[input.key] =
      fixtureOverrides[input.key]
      ?? defaultSimulationValueForInput(input, catalog)
  }
  return { ...values, ...fixtureOverrides }
}
