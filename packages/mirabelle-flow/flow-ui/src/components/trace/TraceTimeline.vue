<script setup lang="ts">
import { parseTraceJson } from '@mirabelle/flow-core'
import { ref } from 'vue'
import { useHaConnection } from '@/composables/useHaConnection'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const ha = useHaConnection()
const traceJson = ref('')
const automationId = ref('')
const selectedRunId = ref('')
const runs = ref<{ run_id: string, timestamp: string, state: string }[]>([])

async function loadRuns() {
  if (!automationId.value) {
    return
  }
  const itemId = automationId.value.replace(/^automation\./, '')
  runs.value = await ha.listTraces('automation', itemId)
}

async function loadTraceRun() {
  if (!automationId.value || !selectedRunId.value) {
    return
  }
  const itemId = automationId.value.replace(/^automation\./, '')
  const data = await ha.getTrace('automation', itemId, selectedRunId.value)
  store.setTrace(parseTraceJson(data))
}

function importLocalTrace() {
  try {
    const data = JSON.parse(traceJson.value)
    store.setTrace(parseTraceJson(data))
  }
  catch (e) {
    alert(e instanceof Error ? e.message : 'Invalid trace JSON')
  }
}
</script>

<template>
  <div class="flex h-full flex-col border-t border-neutral-800 bg-neutral-900 p-2">
    <h3 class="mb-2 text-xs font-medium text-neutral-400">
      Trace timeline
    </h3>

    <div class="mb-2 flex flex-wrap gap-2">
      <input
        v-model="automationId"
        placeholder="automation.id"
        class="rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
      >
      <button
        type="button"
        class="rounded bg-neutral-700 px-2 py-1 text-xs"
        @click="loadRuns"
      >
        List runs
      </button>
      <select
        v-model="selectedRunId"
        class="rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
      >
        <option value="">
          Select run
        </option>
        <option v-for="r in runs" :key="r.run_id" :value="r.run_id">
          {{ r.timestamp }} — {{ r.state }}
        </option>
      </select>
      <button
        type="button"
        class="rounded bg-emerald-800 px-2 py-1 text-xs"
        @click="loadTraceRun"
      >
        Load trace
      </button>
    </div>

    <ol
      v-if="store.traceOverlay?.steps.length"
      class="mb-2 max-h-24 flex-1 overflow-y-auto text-xs"
    >
      <li
        v-for="(step, i) in store.traceOverlay.steps"
        :key="i"
        class="border-l-2 border-yellow-500 py-0.5 pl-2"
        :class="store.highlightedNodeIds.has(step.path.replace(/\//g, '_')) ? 'text-yellow-300' : 'text-neutral-400'"
      >
        <span class="font-mono">{{ step.path }}</span>
        <span v-if="step.result" class="ml-2 text-neutral-500">{{ step.result }}</span>
      </li>
    </ol>

    <details class="text-xs">
      <summary class="cursor-pointer text-neutral-500">
        Import trace JSON (local dev)
      </summary>
      <textarea
        v-model="traceJson"
        class="mt-1 h-16 w-full rounded border border-neutral-700 bg-neutral-950 p-1 font-mono"
        placeholder='{"trace": {...}}'
      />
      <button
        type="button"
        class="mt-1 rounded bg-neutral-700 px-2 py-1"
        @click="importLocalTrace"
      >
        Import
      </button>
    </details>
  </div>
</template>
