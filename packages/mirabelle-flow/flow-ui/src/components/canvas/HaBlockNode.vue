<script setup lang="ts">
import { computed } from 'vue'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, card, title, label, icon } = useFlowNodeUi(() => props.data)

const isContainer = computed(() => props.data.rawData?.isContainer === true)
const blockKey = computed(() => String(props.data.rawData?.blockKey ?? ''))
</script>

<template>
  <div :class="card()">
    <FlowNodeHandles
      :handles="data.handles"
      target-class="!bg-neutral-500"
      target-top-class="!bg-violet-300"
    />
    <div :class="title('flex items-center gap-1.5')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span v-if="isContainer" class="capitalize">{{ blockKey || data.label }}</span>
      <span v-else :class="label('text-[11px]')">{{ data.label }}</span>
    </div>
  </div>
</template>
