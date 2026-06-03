<script setup lang="ts">
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, card, title, icon } = useFlowNodeUi(() => props.data)
</script>

<template>
  <div :class="card()">
    <div :class="title('flex items-center gap-1.5')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span class="capitalize">Variables</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
  </div>
</template>
