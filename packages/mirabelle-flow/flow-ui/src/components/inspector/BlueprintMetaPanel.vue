<script setup lang="ts">
import type { BlueprintInputDef } from '@mirabelle/flow-shared'
import { Label } from 'reka-ui'
import { computed } from 'vue'
import { useEntityPicker } from '@/composables/useEntityPicker'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const picker = useEntityPicker()

const metaNode = computed(() =>
  store.document?.nodes.find(n => n.kind === 'blueprint_meta'),
)

const inputs = computed(
  () =>
    (metaNode.value?.data.inputs as BlueprintInputDef[] | undefined)
    ?? store.document?.blueprintMeta?.inputs
    ?? [],
)

const simulationValues = computed(() => {
  const fromNode = metaNode.value?.data.simulationValues as
    | Record<string, unknown>
    | undefined
  return fromNode ?? store.previewInputs
})

function valueFor(key: string): string {
  const v = simulationValues.value[key]
  if (v === undefined || v === null) {
    return ''
  }
  if (Array.isArray(v)) {
    return v.join(', ')
  }
  return String(v)
}

function updateInput(key: string, raw: string) {
  store.setSimulationInput(key, raw)
}

function isEntityInput(input: BlueprintInputDef): boolean {
  const domain = picker.selectorDomain(input.selector)
  return domain !== undefined && domain !== 'device'
}
</script>

<template>
  <div v-if="metaNode" class="flex flex-col gap-4 overflow-y-auto p-4">
    <div>
      <div class="text-xs text-neutral-500">
        blueprint_meta
      </div>
      <h2 class="text-lg font-semibold text-pink-300">
        {{ metaNode.label }}
      </h2>
      <p
        v-if="store.document?.blueprintMeta?.description"
        class="mt-1 text-xs text-neutral-400"
      >
        {{ store.document.blueprintMeta.description }}
      </p>
    </div>

    <div class="rounded border border-pink-900/40 bg-pink-950/30 p-3">
      <label class="flex items-center gap-2 text-sm">
        <input
          v-model="store.previewMode"
          type="checkbox"
          @change="store.applySimulation()"
        >
        <span>Simulation mode</span>
      </label>
      <p class="mt-1 text-xs text-neutral-500">
        Substitutes inputs into the graph and enriches node labels.
      </p>
    </div>

    <div>
      <h3 class="mb-2 text-sm font-medium text-pink-200">
        Blueprint inputs
      </h3>
      <div
        v-for="input in inputs"
        :key="input.key"
        class="mb-3 rounded border border-neutral-800 bg-neutral-900/80 p-2"
      >
        <Label class="text-xs text-neutral-300">{{ input.name ?? input.key }}</Label>
        <p v-if="input.description" class="mb-1 text-[10px] text-neutral-500">
          {{ input.description }}
        </p>
        <template v-if="isEntityInput(input)">
          <select
            class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
            :value="valueFor(input.key)"
            @change="updateInput(input.key, ($event.target as HTMLSelectElement).value)"
          >
            <option value="">
              — select —
            </option>
            <option
              v-for="opt in picker.optionsForDomain(picker.selectorDomain(input.selector))"
              :key="opt.id"
              :value="opt.id"
            >
              {{ opt.label }}
            </option>
          </select>
          <input
            class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
            placeholder="Or type entity id"
            :value="valueFor(input.key)"
            @change="updateInput(input.key, ($event.target as HTMLInputElement).value)"
          >
        </template>
        <input
          v-else
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs"
          :value="valueFor(input.key)"
          @change="updateInput(input.key, ($event.target as HTMLInputElement).value)"
        >
        <button
          type="button"
          class="mt-1 text-[10px] text-cyan-400 hover:underline"
          @click="store.highlightInputBindings(input.key)"
        >
          Show usages on graph
        </button>
      </div>
      <button
        type="button"
        class="w-full rounded bg-emerald-900/60 py-1.5 text-sm text-emerald-200 hover:bg-emerald-800/60"
        @click="store.applySimulation()"
      >
        Apply simulation
      </button>
    </div>
  </div>
</template>
