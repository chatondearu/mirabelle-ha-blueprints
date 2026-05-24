import {
  createConnection,
  subscribeEntities,
  type Connection,
  type HassEntity,
  type MessageBase,
} from 'home-assistant-js-websocket'
import { ref, shallowRef } from 'vue'

export interface HaAutomationConfig {
  id: string
  alias?: string
  description?: string
}

const connection = shallowRef<Connection | null>(null)
const connected = ref(false)
const error = ref<string | null>(null)
const entities = shallowRef<Record<string, HassEntity>>({})

export function useHaConnection() {
  async function connect(url?: string, token?: string): Promise<void> {
    const hassUrl = url ?? import.meta.env.VITE_HA_URL ?? window.hassUrl

    if (!hassUrl) {
      error.value = 'No Home Assistant URL configured'
      return
    }

    try {
      if (token ?? window.hassToken) {
        const accessToken = token ?? window.hassToken!
        connection.value = await createConnection({
          auth: {
            access_token: accessToken,
            expires: Date.now() + 86400000,
            hassUrl,
            refresh_token: '',
            client_id: 'mirabelle-flow',
            token_type: 'Bearer',
          } as never,
        })
      }
      else {
        // Panel mode: HA session cookie auth via /auth/token
        connection.value = await createConnection({
          auth: async () => {
            const resp = await fetch('/auth/token', {
              method: 'POST',
              credentials: 'include',
            })
            if (!resp.ok) {
              throw new Error('Not authenticated with Home Assistant')
            }
            return resp.json()
          },
        } as unknown as Parameters<typeof createConnection>[0])
      }
      connected.value = true
      error.value = null
      subscribeEntities(connection.value, (ent) => {
        entities.value = ent
      })
    }
    catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      connected.value = false
    }
  }

  async function callWs<T>(message: MessageBase): Promise<T> {
    if (!connection.value) {
      throw new Error('Not connected to Home Assistant')
    }
    return connection.value.sendMessagePromise(message) as Promise<T>
  }

  async function listAutomations(): Promise<HaAutomationConfig[]> {
    return callWs<HaAutomationConfig[]>({
      type: 'config/automation/config/list',
    })
  }

  async function getAutomation(id: string): Promise<Record<string, unknown>> {
    return callWs<Record<string, unknown>>({
      type: 'config/automation/config/get',
      automation_id: id,
    })
  }

  async function updateAutomation(
    id: string,
    config: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return callWs({
      type: 'config/automation/config/update',
      automation_id: id,
      ...config,
    } as MessageBase)
  }

  async function listScripts(): Promise<{ id: string, alias?: string }[]> {
    return callWs({ type: 'config/script/config/list' })
  }

  async function getScript(id: string): Promise<Record<string, unknown>> {
    return callWs({
      type: 'config/script/config/get',
      script_id: id,
    })
  }

  async function listTraces(
    domain: string,
    itemId: string,
  ): Promise<{ run_id: string, timestamp: string, state: string }[]> {
    const result = await callWs<Record<string, { run_id: string, timestamp: string, state: string }>>({
      type: 'trace/list',
      domain,
      item_id: itemId,
    })
    return Object.values(result ?? {})
  }

  async function getTrace(
    domain: string,
    itemId: string,
    runId: string,
  ): Promise<Record<string, unknown>> {
    return callWs({
      type: 'trace/get',
      domain,
      item_id: itemId,
      run_id: runId,
    })
  }

  async function getLayout(key: string): Promise<Record<string, { x: number, y: number }> | null> {
    try {
      const stored = await callWs<{ layout?: Record<string, { x: number, y: number }> }>({
        type: 'mirabelle_flow/layout/get',
        key,
      } as MessageBase)
      if (stored?.layout && typeof stored.layout === 'object') {
        return stored.layout
      }
    }
    catch {
      const raw = localStorage.getItem(`mirabelle_flow_layout_${key}`)
      if (raw) {
        return JSON.parse(raw) as Record<string, { x: number, y: number }>
      }
    }
    return null
  }

  async function saveLayout(
    key: string,
    layout: Record<string, { x: number, y: number }>,
  ): Promise<void> {
    try {
      await callWs({
        type: 'mirabelle_flow/layout/save',
        key,
        layout,
      } as MessageBase)
    }
    catch {
      localStorage.setItem(`mirabelle_flow_layout_${key}`, JSON.stringify(layout))
    }
  }

  function disconnect() {
    connection.value?.close()
    connection.value = null
    connected.value = false
  }

  return {
    connection,
    connected,
    error,
    entities,
    connect,
    disconnect,
    listAutomations,
    getAutomation,
    updateAutomation,
    listScripts,
    getScript,
    listTraces,
    getTrace,
    getLayout,
    saveLayout,
  }
}
