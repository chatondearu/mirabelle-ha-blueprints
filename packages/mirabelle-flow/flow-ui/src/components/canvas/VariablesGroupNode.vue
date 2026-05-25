<script setup lang="ts">
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)
</script>

<template>
  <div
    class="flow-node-group flow-node-card"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="visuals.iconClass" aria-hidden="true" />
      <span>Variables</span>
    </div>
    <div class="mt-1 text-xs text-neutral-400">
      {{ data.label }}
    </div>
  </div>
</template>
