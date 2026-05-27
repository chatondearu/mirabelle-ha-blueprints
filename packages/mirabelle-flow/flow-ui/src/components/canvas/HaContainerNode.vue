<script setup lang="ts">
import { useNodeVisuals } from './composables/useNodeVisuals'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, stateClasses, titleKind } = useNodeVisuals(() => props.data)
</script>

<template>
  <div
    class="flow-node-group flow-node-card"
    :data-kind="data.kind"
    :data-block-key="data.rawData?.blockKey"
    :class="stateClasses"
  >
    <FlowNodeHandles
      :handles="data.handles"
      target-class="!bg-neutral-500"
      target-top-class="!bg-violet-300"
    />
    <div class="flex items-center gap-1.5 font-medium capitalize">
      <span class="flow-node-card__icon" :class="iconClass" aria-hidden="true" />
      <span>{{ titleKind }}</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
  </div>
</template>
