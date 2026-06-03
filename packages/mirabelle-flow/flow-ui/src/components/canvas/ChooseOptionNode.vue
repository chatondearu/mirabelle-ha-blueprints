<script setup lang="ts">
import { computed } from 'vue'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { card } = useFlowNodeUi(() => props.data)

const isDefault = computed(() => props.data.rawData?.isDefault === true)
</script>

<template>
  <div :class="card('min-w-32')">
    <FlowNodeHandles :handles="data.handles" />
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
