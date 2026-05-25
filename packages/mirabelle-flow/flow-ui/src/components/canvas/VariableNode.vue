<script setup lang="ts">
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { stateClasses } = useNodeVisuals(() => props.data)

const varName = computed(() => String(props.data.rawData?.name ?? props.data.label))
</script>

<template>
  <div
    class="flow-node-card flow-node-card--child min-w-32"
    :data-kind="data.kind"
    :class="stateClasses"
  >
    <FlowNodeHandles
      :handles="data.handles"
      :source-id="`var-${varName}`"
      source-class="!bg-neutral-300"
    />
    <div class="text-[11px] font-medium text-teal-200">
      {{ varName }}
    </div>
    <div class="mt-0.5 truncate text-[10px] text-neutral-400">
      {{ data.label }}
    </div>
  </div>
</template>
