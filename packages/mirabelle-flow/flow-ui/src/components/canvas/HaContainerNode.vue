<script setup lang="ts">
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, titleKind, card, title, label, icon } = useFlowNodeUi(() => props.data)
</script>

<template>
  <div :class="card()">
    <FlowNodeHandles
      :handles="data.handles"
      target-class="!bg-neutral-500"
      target-top-class="!bg-violet-300"
    />
    <div :class="title('flex items-center gap-1.5 capitalize')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span>{{ titleKind }}</span>
    </div>
    <div :class="label('mt-1 text-xs')">
      {{ data.label }}
    </div>
  </div>
</template>
