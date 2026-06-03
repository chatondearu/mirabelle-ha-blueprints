<script setup lang="ts">
import type { FlowListItem } from '@mirabelle/flow-shared'
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import {
  handleTop,
  isHighlightedItem,
  itemDisplayValue,
} from './composables/useListNodeHelpers'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, titleKind, card, title, icon } = useFlowNodeUi(() => props.data)

const listItems = computed<FlowListItem[]>(() => {
  const items = props.data.rawData?.items
  return Array.isArray(items) ? (items as FlowListItem[]) : []
})
</script>

<template>
  <div :class="card('max-w-none w-64')">
    <Handle type="target" :position="Position.Left" class="!bg-neutral-400" />
    <div :class="title('flex items-center gap-1.5 capitalize')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span>{{ titleKind }}</span>
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
        <div class="mt-0.5 truncate text-[10px] text-neutral-400">
          {{ itemDisplayValue(item) || '—' }}
        </div>
        <Handle
          type="source"
          :position="Position.Right"
          :id="`var-${item.key}`"
          class="!bg-neutral-300"
          :style="{ top: handleTop(idx) }"
        />
      </div>
    </div>
  </div>
</template>
