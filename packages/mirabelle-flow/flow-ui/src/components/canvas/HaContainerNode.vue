<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)

const branchHandles = computed(() => {
  const options = props.data.rawData?.options as
    | Array<{ key: string, label?: string, hasSequence?: boolean }>
    | undefined
  if (!options?.length) {
    return []
  }
  const withFlow = options.filter(o => o.hasSequence !== false)
  const count = withFlow.length
  return withFlow.map((opt, index) => ({
    ...opt,
    top:
      count === 1
        ? '50%'
        : `${((index + 1) / (count + 1)) * 100}%`,
  }))
})
</script>

<template>
  <div
    class="flow-node-group flow-node-card"
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
    <Handle
      v-for="opt in branchHandles"
      :key="opt.key"
      type="source"
      :position="Position.Right"
      :id="opt.key"
      class="!bg-neutral-400"
      :style="{ top: opt.top }"
    />
    <Handle
      v-if="branchHandles.length === 0"
      type="source"
      :position="Position.Right"
      id="flow"
      class="!bg-neutral-400"
      style="top: 50%"
    />
  </div>
</template>
