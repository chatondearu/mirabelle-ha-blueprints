<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)

const optKey = computed(() => String(props.data.rawData?.key ?? ''))
const conditions = computed(
  () => props.data.rawData?.conditions as unknown[] | undefined,
)
</script>

<template>
  <div
    class="flow-node-card flow-node-card--child min-w-36"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <Handle
      type="target"
      :position="Position.Left"
      :id="`cond-${optKey}`"
      class="!bg-purple-300"
    />
    <div class="truncate text-[11px] font-medium text-purple-200">
      {{ data.label }}
    </div>
    <div class="truncate text-[10px] text-neutral-500">
      {{ Array.isArray(conditions) ? conditions.length : 0 }} condition(s)
    </div>
    <Handle
      type="source"
      :position="Position.Right"
      :id="optKey"
      class="!bg-purple-300"
    />
  </div>
</template>
