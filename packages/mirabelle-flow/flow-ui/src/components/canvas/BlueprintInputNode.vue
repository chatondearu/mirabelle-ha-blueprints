<script setup lang="ts">
import { computed } from 'vue'
import { useEntityPicker } from '@/composables/useEntityPicker'
import { useFlowStore } from '@/stores/flow'
import { itemDisplayValue } from './composables/useListNodeHelpers'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const store = useFlowStore()
const picker = useEntityPicker()
const { card } = useFlowNodeUi(() => props.data)

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
  <div :class="card('min-w-36')">
    <FlowNodeHandles
      :handles="data.handles"
      :source-id="`inp-${key}`"
      source-class="!bg-neutral-300"
    />
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
  </div>
</template>
