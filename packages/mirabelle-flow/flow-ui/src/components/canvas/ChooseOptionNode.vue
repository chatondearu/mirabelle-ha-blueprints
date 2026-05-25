<script setup lang="ts">
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)

const isDefault = computed(() => props.data.rawData?.isDefault === true)
</script>

<template>
  <div
    class="flow-node-card flow-node-card--child min-w-32"
    :data-kind="data.kind"
    :class="visuals.stateClasses"
  >
    <div
      class="text-[11px] font-medium"
      :class="isDefault ? 'text-purple-200' : 'text-neutral-400'"
    >
      {{ data.label }}
    </div>
    <div v-if="isDefault" class="text-[10px] text-neutral-500">
      fallback branch
    </div>
  </div>
</template>
