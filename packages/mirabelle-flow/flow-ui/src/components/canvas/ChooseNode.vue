<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import { handleTop, isHighlightedItem } from './composables/useListNodeHelpers'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)

const chooseOptions = computed<Array<{ key: string; label: string; conditions: unknown[] }>>(() => {
  const options = props.data.rawData?.options
  return Array.isArray(options)
    ? (options as Array<{ key: string; label: string; conditions: unknown[] }>)
    : []
})
</script>

<template>
  <div
    class="flow-node-card"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <Handle type="target" :position="Position.Left" class="!bg-neutral-400" />
    <div class="flex items-center gap-1.5 font-medium capitalize">
      <span class="flow-node-card__icon" :class="visuals.iconClass" aria-hidden="true" />
      <span>{{ visuals.titleKind }}</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
    <div class="mt-2 space-y-1 border-t border-neutral-700/70 pt-2">
      <div
        v-for="(opt, idx) in chooseOptions"
        :key="opt.key"
        class="rounded px-1 py-1 text-[11px]"
        :class="[
          isHighlightedItem(data, opt.key) ? 'bg-emerald-900/45 font-semibold text-emerald-200' : 'text-neutral-300',
          data.pathActive && !isHighlightedItem(data, opt.key) ? 'opacity-50' : '',
        ]"
      >
        <div class="truncate">{{ opt.label }}</div>
        <div class="truncate text-[10px] text-neutral-500">
          {{ Array.isArray(opt.conditions) ? opt.conditions.length : 0 }} condition(s)
        </div>
        <Handle
          type="target"
          :position="Position.Left"
          :id="`cond-${opt.key}`"
          class="!bg-purple-300"
          :style="{ top: handleTop(idx) }"
        />
        <Handle
          type="source"
          :position="Position.Right"
          :id="opt.key"
          class="!bg-purple-300"
          :style="{ top: handleTop(idx) }"
        />
      </div>
      <div class="rounded px-1 py-1 text-[11px] text-neutral-400">
        Default
        <Handle
          type="source"
          :position="Position.Right"
          id="opt-default"
          class="!bg-neutral-300"
          :style="{ top: handleTop(chooseOptions.length) }"
        />
      </div>
    </div>
  </div>
</template>

