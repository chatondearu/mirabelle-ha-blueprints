import type { HassEntity } from 'home-assistant-js-websocket'
import { computed } from 'vue'
import { useHaConnection } from '@/composables/useHaConnection'
import { useFlowStore } from '@/stores/flow'

export interface EntityOption {
  id: string
  label: string
  domain: string
}

function entityDomain(entityId: string): string {
  return entityId.split('.')[0] ?? ''
}

export function useEntityPicker() {
  const ha = useHaConnection()
  const store = useFlowStore()

  const catalogOptions = computed<EntityOption[]>(() => {
    const c = store.simulationCatalog
    const options: EntityOption[] = []
    for (const id of c.lights) {
      options.push({ id, label: id, domain: 'light' })
    }
    for (const id of c.sensors) {
      options.push({ id, label: id, domain: 'binary_sensor' })
    }
    for (const id of c.switches) {
      options.push({ id, label: id, domain: 'switch' })
    }
    for (const id of c.media_players) {
      options.push({ id, label: id, domain: 'media_player' })
    }
    for (const id of c.alarm_control_panels) {
      options.push({ id, label: id, domain: 'alarm_control_panel' })
    }
    return options
  })

  const haOptions = computed<EntityOption[]>(() => {
    const ent = ha.entities.value as Record<string, HassEntity>
    return Object.keys(ent)
      .sort()
      .map(id => ({
        id,
        label: `${id} (${ent[id]?.state ?? '?'})`,
        domain: entityDomain(id),
      }))
  })

  function optionsForDomain(domain?: string): EntityOption[] {
    const haList = ha.connected.value ? haOptions.value : []
    const local = catalogOptions.value
    const merged = new Map<string, EntityOption>()
    for (const o of haList) {
      if (!domain || o.domain === domain) {
        merged.set(o.id, o)
      }
    }
    for (const o of local) {
      if (!domain || o.domain === domain) {
        if (!merged.has(o.id)) {
          merged.set(o.id, o)
        }
      }
    }
    return [...merged.values()]
  }

  function selectorDomain(selector?: Record<string, unknown>): string | undefined {
    const entity = selector?.entity as { filter?: { domain?: string }[] } | undefined
    const filters = entity?.filter
    if (Array.isArray(filters)) {
      return filters.find(f => f?.domain)?.domain
    }
    const device = selector?.device as { filter?: { integration?: string }[] } | undefined
    if (device) {
      return 'device'
    }
    return undefined
  }

  return {
    connected: ha.connected,
    optionsForDomain,
    selectorDomain,
    catalogOptions,
    haOptions,
  }
}
