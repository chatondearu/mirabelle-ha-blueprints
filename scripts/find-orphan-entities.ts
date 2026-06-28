#!/usr/bin/env node
/**
 * Script to find Home Assistant entities that are still registered but should
 * no longer exist (orphans / ghost entities).
 *
 * It cross-references three data sources from a live HA instance:
 *  1. Entity registry  (WebSocket: config/entity_registry/list)
 *  2. Config entries    (WebSocket: config_entries/get)
 *  3. Current states     (REST:      /api/states)
 *
 * An entity is flagged when either:
 *  - its `config_entry_id` points to a config entry that no longer exists
 *    (the integration instance was removed) -> high confidence orphan, or
 *  - it is "unavailable" with the `restored: true` attribute, meaning HA restored
 *    it from the registry but no integration re-created it (ghost entity), or
 *  - it has no live state and is not disabled/hidden by design
 *    (registered but not provided by any integration) -> likely orphan.
 *
 * Usage:
 *   pnpm run find-orphan-entities
 *   pnpm run find-orphan-entities -- --json
 *   pnpm run find-orphan-entities -- --json > orphans.json
 */

import { config } from 'dotenv'
import axios from 'axios'

config()

// Configuration
const HA_URL = process.env.HA_URL || 'http://supervisor/core'
const HA_TOKEN = process.env.HA_TOKEN
const HA_VERIFY_SSL = process.env.HA_VERIFY_SSL !== 'false'
const HA_TIMEOUT = parseInt(process.env.HA_TIMEOUT || '30', 10)

const OUTPUT_JSON = process.argv.includes('--json')

// When SSL verification is disabled (self-signed certs), also relax it for the
// native WebSocket client which has no per-connection option for this.
if (!HA_VERIFY_SSL) {
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'
}

// Types describing the subset of HA API payloads we rely on.
interface EntityRegistryEntry {
  entity_id: string
  unique_id: string
  platform: string
  config_entry_id: string | null
  device_id: string | null
  area_id: string | null
  disabled_by: string | null
  hidden_by: string | null
  entity_category: string | null
  name: string | null
  original_name: string | null
}

interface ConfigEntry {
  entry_id: string
  domain: string
  title: string
  state: string
}

interface HassState {
  entity_id: string
  state: string
  attributes?: { restored?: boolean }
}

type OrphanReason = 'config_entry_removed' | 'restored_unavailable' | 'no_live_state'

interface OrphanEntity {
  entity_id: string
  platform: string
  reason: OrphanReason
  config_entry_id: string | null
  config_entry_state: string | null
  config_entry_title: string | null
  disabled_by: string | null
  hidden_by: string | null
  name: string | null
  details: string
}

// REST client (mirrors the other scripts in this repo).
const api = axios.create({
  baseURL: HA_URL,
  headers: {
    Authorization: `Bearer ${HA_TOKEN}`,
    'Content-Type': 'application/json',
  },
  timeout: HA_TIMEOUT * 1000,
  httpsAgent: HA_VERIFY_SSL ? undefined : new (require('https').Agent)({ rejectUnauthorized: false }),
})

/**
 * Build the WebSocket URL from the configured HA REST URL.
 */
function buildWebSocketUrl(): string {
  const wsUrl = HA_URL.replace(/^http/i, 'ws').replace(/\/+$/, '')
  return `${wsUrl}/api/websocket`
}

/**
 * Connect to the HA WebSocket API, authenticate, run the given commands in
 * order and resolve with their results.
 */
function fetchViaWebSocket<T extends Record<string, string>>(
  commandsByKey: T,
): Promise<Record<keyof T, unknown>> {
  const WebSocketCtor: typeof globalThis.WebSocket | undefined = (globalThis as { WebSocket?: typeof globalThis.WebSocket }).WebSocket

  return new Promise((resolve, reject) => {
    if (!WebSocketCtor) {
      reject(new Error('Global WebSocket is unavailable. Node.js 21 or later is required.'))
      return
    }

    const keys = Object.keys(commandsByKey) as (keyof T)[]
    const results = {} as Record<keyof T, unknown>
    // Map the message id sent to HA back to the logical result key.
    const idToKey = new Map<number, keyof T>()
    let nextId = 1
    let authenticated = false

    const socket = new WebSocketCtor(buildWebSocketUrl())

    const timer = setTimeout(() => {
      socket.close()
      reject(new Error(`WebSocket request timed out after ${HA_TIMEOUT}s`))
    }, HA_TIMEOUT * 1000)

    const finish = (error?: Error) => {
      clearTimeout(timer)
      try {
        socket.close()
      } catch {
        // ignore close errors
      }
      if (error) {
        reject(error)
      } else {
        resolve(results)
      }
    }

    socket.addEventListener('error', () => {
      finish(new Error('WebSocket connection error. Check HA_URL and network access.'))
    })

    socket.addEventListener('message', (event: MessageEvent) => {
      let message: { type: string, id?: number, success?: boolean, result?: unknown, error?: { message?: string } }
      try {
        message = JSON.parse(String(event.data))
      } catch {
        return
      }

      if (message.type === 'auth_required') {
        socket.send(JSON.stringify({ type: 'auth', access_token: HA_TOKEN }))
        return
      }

      if (message.type === 'auth_invalid') {
        finish(new Error('WebSocket authentication failed. Check HA_TOKEN.'))
        return
      }

      if (message.type === 'auth_ok') {
        authenticated = true
        for (const key of keys) {
          const id = nextId++
          idToKey.set(id, key)
          socket.send(JSON.stringify({ id, type: commandsByKey[key] }))
        }
        return
      }

      if (message.type === 'result' && typeof message.id === 'number') {
        const key = idToKey.get(message.id)
        if (key === undefined) {
          return
        }
        if (!message.success) {
          finish(new Error(`Command "${commandsByKey[key]}" failed: ${message.error?.message ?? 'unknown error'}`))
          return
        }
        results[key] = message.result
        idToKey.delete(message.id)
        if (idToKey.size === 0) {
          finish()
        }
      }
    })

    socket.addEventListener('close', () => {
      if (!authenticated) {
        finish(new Error('WebSocket closed before authentication completed.'))
      }
    })
  })
}

/**
 * Fetch all current states via the REST API.
 */
async function getStates(): Promise<HassState[]> {
  const response = await api.get<HassState[]>('/api/states')
  return response.data
}

/**
 * Decide whether a registry entry is an orphan and, if so, why.
 */
function classifyEntity(
  entry: EntityRegistryEntry,
  validConfigEntryIds: Set<string>,
  configEntryById: Map<string, ConfigEntry>,
  stateById: Map<string, HassState>,
): OrphanEntity | null {
  const entryInfo = entry.config_entry_id ? configEntryById.get(entry.config_entry_id) : undefined
  const base = {
    entity_id: entry.entity_id,
    platform: entry.platform,
    config_entry_id: entry.config_entry_id,
    config_entry_state: entryInfo?.state ?? null,
    config_entry_title: entryInfo?.title ?? null,
    disabled_by: entry.disabled_by,
    hidden_by: entry.hidden_by,
    name: entry.name ?? entry.original_name,
  }

  // 1. Its config entry was removed -> the integration instance is gone.
  if (entry.config_entry_id && !validConfigEntryIds.has(entry.config_entry_id)) {
    return {
      ...base,
      reason: 'config_entry_removed',
      details: `config_entry_id "${entry.config_entry_id}" no longer exists`,
    }
  }

  const liveState = stateById.get(entry.entity_id)

  // 2. Restored from the registry but no integration re-created it -> ghost entity.
  if (liveState?.attributes?.restored === true) {
    return {
      ...base,
      reason: 'restored_unavailable',
      details: `state "${liveState.state}" with restored=true (not provided by any integration)`,
    }
  }

  // Disabled entities legitimately have no live state; skip the next heuristic.
  if (entry.disabled_by) {
    return null
  }

  // 3. Registered but no live state at all -> not currently provided.
  if (!liveState) {
    const context = entryInfo
      ? `integration "${entryInfo.domain}" (state: ${entryInfo.state})`
      : `platform "${entry.platform}"`
    return {
      ...base,
      reason: 'no_live_state',
      details: `no live state, from ${context}`,
    }
  }

  return null
}

async function main() {
  if (!HA_TOKEN) {
    console.error('❌ HA_TOKEN is not set in .env file')
    process.exit(1)
  }

  if (!OUTPUT_JSON) {
    console.log('Fetching entity registry and config entries via WebSocket...')
  }

  const wsData = await fetchViaWebSocket({
    entities: 'config/entity_registry/list',
    configEntries: 'config_entries/get',
  })

  const registry = (wsData.entities as EntityRegistryEntry[]) ?? []
  const configEntries = (wsData.configEntries as ConfigEntry[]) ?? []

  if (!OUTPUT_JSON) {
    console.log('Fetching current states via REST...')
  }
  const states = await getStates()

  const validConfigEntryIds = new Set(configEntries.map(entry => entry.entry_id))
  const configEntryById = new Map(configEntries.map(entry => [entry.entry_id, entry]))
  const stateById = new Map(states.map(state => [state.entity_id, state]))

  const orphans: OrphanEntity[] = []
  for (const entry of registry) {
    const orphan = classifyEntity(entry, validConfigEntryIds, configEntryById, stateById)
    if (orphan) {
      orphans.push(orphan)
    }
  }

  // Most actionable reasons first, then alphabetical by entity id.
  const reasonOrder: Record<OrphanReason, number> = {
    config_entry_removed: 0,
    restored_unavailable: 1,
    no_live_state: 2,
  }
  orphans.sort((a, b) => {
    if (a.reason !== b.reason) {
      return reasonOrder[a.reason] - reasonOrder[b.reason]
    }
    return a.entity_id.localeCompare(b.entity_id)
  })

  if (OUTPUT_JSON) {
    // Per config entry: how many of its registered entities are orphan. When
    // every entity of an entry is orphan, the integration instance is dead.
    const totalByEntry = new Map<string, number>()
    for (const entry of registry) {
      if (entry.config_entry_id) {
        totalByEntry.set(entry.config_entry_id, (totalByEntry.get(entry.config_entry_id) ?? 0) + 1)
      }
    }
    const orphanByEntry = new Map<string, number>()
    for (const orphan of orphans) {
      if (orphan.config_entry_id) {
        orphanByEntry.set(orphan.config_entry_id, (orphanByEntry.get(orphan.config_entry_id) ?? 0) + 1)
      }
    }
    const configEntriesSummary = configEntries
      .filter(entry => orphanByEntry.has(entry.entry_id))
      .map(entry => ({
        entry_id: entry.entry_id,
        domain: entry.domain,
        title: entry.title,
        state: entry.state,
        registered_entities: totalByEntry.get(entry.entry_id) ?? 0,
        orphan_entities: orphanByEntry.get(entry.entry_id) ?? 0,
        all_orphan: (totalByEntry.get(entry.entry_id) ?? 0) === (orphanByEntry.get(entry.entry_id) ?? 0),
      }))
      .sort((a, b) => b.orphan_entities - a.orphan_entities)

    console.log(JSON.stringify({
      generated_at: new Date().toISOString(),
      total_registered: registry.length,
      total_orphans: orphans.length,
      config_entries_summary: configEntriesSummary,
      orphans,
    }, null, 2))
    return
  }

  const removedEntry = orphans.filter(o => o.reason === 'config_entry_removed')
  const restored = orphans.filter(o => o.reason === 'restored_unavailable')
  const noState = orphans.filter(o => o.reason === 'no_live_state')

  console.log(`\nRegistered entities: ${registry.length}`)
  console.log(`Potential orphans:   ${orphans.length}\n`)

  const printGroup = (title: string, items: OrphanEntity[]) => {
    console.log(`${title} (${items.length})`)
    console.log('='.repeat(title.length + 6))
    if (items.length === 0) {
      console.log('  none\n')
      return
    }
    for (const item of items) {
      const flags: string[] = []
      if (item.disabled_by) flags.push(`disabled_by=${item.disabled_by}`)
      if (item.hidden_by) flags.push(`hidden_by=${item.hidden_by}`)
      const suffix = flags.length ? ` [${flags.join(', ')}]` : ''
      console.log(`  • ${item.entity_id}${suffix}`)
      console.log(`      ${item.details}`)
    }
    console.log('')
  }

  printGroup('Integration removed (high confidence)', removedEntry)
  printGroup('Restored & unavailable (ghost entities)', restored)
  printGroup('No live state (likely orphan)', noState)

  console.log('Note: review before deleting. A "restored/unavailable" or "no live state"')
  console.log('entity can also be a temporarily offline device. Delete confirmed orphans from')
  console.log('HA via Settings → Devices & Services → Entities.')
}

main().catch((error) => {
  console.error('Fatal error:', error instanceof Error ? error.message : error)
  process.exit(1)
})
