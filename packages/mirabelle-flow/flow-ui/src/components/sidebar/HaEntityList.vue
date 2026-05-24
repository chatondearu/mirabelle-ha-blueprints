<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useHaConnection } from '@/composables/useHaConnection'
import { stringify } from 'yaml'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const ha = useHaConnection()
const automations = ref<{ id: string, alias?: string }[]>([])
const scripts = ref<{ id: string, alias?: string }[]>([])
const loading = ref(false)

onMounted(async () => {
  if (!ha.connected.value) {
    await ha.connect()
  }
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    automations.value = await ha.listAutomations()
    scripts.value = await ha.listScripts()
  }
  finally {
    loading.value = false
  }
}

async function loadAutomation(id: string) {
  const config = await ha.getAutomation(id)
  const yaml = stringify(config)
  const layoutKey = `automation:${id}`
  store.loadYaml(yaml, `automation:${id}`)
  store.document!.source = layoutKey
  const saved = await ha.getLayout(layoutKey)
  if (saved && store.document) {
    store.document.layout = { ...store.document.layout, ...saved }
  }
}

async function loadScript(id: string) {
  const config = await ha.getScript(id)
  const yaml = stringify(config)
  store.loadYaml(yaml, `script:${id}`)
}
</script>

<template>
  <div class="flex h-full flex-col p-2">
    <div class="mb-2 flex items-center justify-between">
      <span class="text-xs font-medium text-neutral-400">Home Assistant</span>
      <button
        type="button"
        class="text-xs text-emerald-500 hover:underline"
        :disabled="loading"
        @click="refresh"
      >
        Refresh
      </button>
    </div>
    <p v-if="ha.error.value" class="mb-2 text-xs text-red-400">
      {{ ha.error.value }}
    </p>
    <p v-if="!ha.connected.value" class="text-xs text-neutral-500">
      Connect from HA panel or set VITE_HA_URL + token for dev.
    </p>
    <section v-if="automations.length" class="mb-3">
      <h3 class="mb-1 text-xs text-neutral-500">
        Automations
      </h3>
      <ul class="space-y-1">
        <li v-for="a in automations" :key="a.id">
          <button
            type="button"
            class="w-full truncate rounded px-2 py-1 text-left text-xs hover:bg-neutral-800"
            @click="loadAutomation(a.id)"
          >
            {{ a.alias ?? a.id }}
          </button>
        </li>
      </ul>
    </section>
    <section v-if="scripts.length">
      <h3 class="mb-1 text-xs text-neutral-500">
        Scripts
      </h3>
      <ul class="space-y-1">
        <li v-for="s in scripts" :key="s.id">
          <button
            type="button"
            class="w-full truncate rounded px-2 py-1 text-left text-xs hover:bg-neutral-800"
            @click="loadScript(s.id)"
          >
            {{ s.alias ?? s.id }}
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>
