<script setup lang="ts">
import type { FlowListItem } from '@mirabelle/flow-shared'
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import { useEntityPicker } from '@/composables/useEntityPicker'
import { useFlowStore } from '@/stores/flow'
import {
  handleTop,
  isHighlightedItem,
  itemDisplayValue,
} from './composables/useListNodeHelpers'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const store = useFlowStore()
const picker = useEntityPicker()
const visuals = useNodeVisuals(props.data)

const listItems = computed<FlowListItem[]>(() => {
  const items = props.data.rawData?.items
  return Array.isArray(items) ? (items as FlowListItem[]) : []
})

function selectorDomain(item: FlowListItem): string | undefined {
  const selector = item.meta?.selector as Record<string, unknown> | undefined
  return picker.selectorDomain(selector)
}

function updateInput(item: FlowListItem, value: string): void {
  store.setSimulationInput(item.key, value)
  store.applySimulation()
}
</script>

<template>
  <div
    class="flow-node-card"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <div class="flex items-center gap-1.5 font-medium capitalize">
      <span class="flow-node-card__icon" :class="visuals.iconClass" aria-hidden="true" />
      <span>{{ visuals.titleKind }}</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
    <div class="mt-2 space-y-1 border-t border-neutral-700/70 pt-2">
      <div
        v-for="(item, idx) in listItems"
        :key="item.key"
        class="rounded px-1 py-1 text-[11px]"
        :class="[
          isHighlightedItem(data, item.key) ? 'bg-emerald-900/45 font-semibold text-emerald-200' : 'text-neutral-300',
          data.pathActive && !isHighlightedItem(data, item.key) ? 'opacity-50' : '',
        ]"
      >
        <div class="flex items-center gap-1">
          <span class="min-w-0 flex-1 truncate">{{ item.label }}</span>
          <span class="text-[10px] text-neutral-500">{{ item.valueType }}</span>
        </div>
        <select
          v-if="selectorDomain(item)"
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-[10px]"
          :value="itemDisplayValue(item)"
          @change="updateInput(item, ($event.target as HTMLSelectElement).value)"
        >
          <option value="">— select —</option>
          <option
            v-for="opt in picker.optionsForDomain(selectorDomain(item))"
            :key="opt.id"
            :value="opt.id"
          >
            {{ opt.id }}
          </option>
        </select>
        <input
          v-else
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-950 px-1 py-0.5 text-[10px]"
          :value="itemDisplayValue(item)"
          @change="updateInput(item, ($event.target as HTMLInputElement).value)"
        >
        <Handle
          type="source"
          :position="Position.Right"
          :id="`inp-${item.key}`"
          class="!bg-neutral-300"
          :style="{ top: handleTop(idx) }"
        />
      </div>
    </div>
  </div>
</template>

