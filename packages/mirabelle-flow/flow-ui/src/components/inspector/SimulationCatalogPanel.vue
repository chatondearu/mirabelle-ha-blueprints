<script setup lang="ts">
import type { SimulationCatalog } from '@mirabelle/flow-shared'
import { ref } from 'vue'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const open = ref(false)

const domains = [
  'lights',
  'sensors',
  'switches',
  'media_players',
  'alarm_control_panels',
] as const

function linesFor(key: keyof SimulationCatalog): string {
  const val = store.simulationCatalog[key]
  if (Array.isArray(val)) {
    return val.join('\n')
  }
  return ''
}

function saveLines(key: keyof SimulationCatalog, text: string) {
  const list = text
    .split('\n')
    .map(s => s.trim())
    .filter(Boolean)
  const next = { ...store.simulationCatalog, [key]: list }
  store.saveSimulationCatalog(next)
}
</script>

<template>
  <div class="border-t border-neutral-800 p-2">
    <button
      type="button"
      class="flex w-full items-center justify-between rounded px-2 py-1 text-xs text-neutral-400 hover:bg-neutral-900"
      @click="open = !open"
    >
      <span>Simulation catalog</span>
      <span>{{ open ? '▼' : '▶' }}</span>
    </button>
    <div v-if="open" class="mt-2 space-y-2 px-1">
      <p class="text-[10px] text-neutral-500">
        Reused as defaults when HA is unavailable. HA entities take priority in pickers when connected.
      </p>
      <div v-for="domain in domains" :key="domain">
        <label class="text-[10px] capitalize text-neutral-400">{{ domain.replace('_', ' ') }}</label>
        <textarea
          class="mt-0.5 h-16 w-full rounded border border-neutral-700 bg-neutral-950 p-1 font-mono text-[10px]"
          :value="linesFor(domain)"
          @change="saveLines(domain, ($event.target as HTMLTextAreaElement).value)"
        />
      </div>
    </div>
  </div>
</template>
