<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { useEntityPicker } from '@/composables/useEntityPicker'
import { useFlowStore } from '@/stores/flow'
import { itemDisplayValue } from './composables/useListNodeHelpers'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const store = useFlowStore()
const picker = useEntityPicker()
const visuals = useNodeVisuals(props.data)

const key = computed(() => String(props.data.rawData?.key ?? ''))
const selector = computed(
  () => props.data.rawData?.selector as Record<string, unknown> | undefined,
)
const domain = computed(() => picker.selectorDomain(selector.value))

const displayValue = computed(() =>
  itemDisplayValue({
    key: key.value,
    label: props.data.label,
    value: props.data.rawData?.value,
    valueType: props.data.rawData?.valueType as string | undefined,
  }),
)

function updateInput(value: string): void {
  store.setSimulationInput(key.value, value)
  store.applySimulation()
}
</script>

<template>
  <div
    class="flow-node-card flow-node-card--child min-w-36"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <div class="text-[11px] font-medium text-pink-200">
      {{ data.label }}
    </div>
    <div class="text-[10px] text-neutral-500">
      {{ data.rawData?.valueType }}
    </div>
    <select
      v-if="domain"
      class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-[10px]"
      :value="displayValue"
      @change="updateInput(($event.target as HTMLSelectElement).value)"
    >
      <option value="">— select —</option>
      <option
        v-for="opt in picker.optionsForDomain(domain)"
        :key="opt.id"
        :value="opt.id"
      >
        {{ opt.id }}
      </option>
    </select>
    <input
      v-else
      class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-[10px]"
      :value="displayValue"
      @change="updateInput(($event.target as HTMLInputElement).value)"
    >
    <Handle
      type="source"
      :position="Position.Right"
      :id="`inp-${key}`"
      class="!bg-neutral-300"
    />
  </div>
</template>
