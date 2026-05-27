<script setup lang="ts">
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, stateClasses } = useNodeVisuals(() => props.data)

const isContainer = computed(() => props.data.rawData?.isContainer === true)
const blockKey = computed(() => String(props.data.rawData?.blockKey ?? ''))
</script>

<template>
  <div
    class="flow-node-card"
    :class="[
      stateClasses,
      isContainer ? 'flow-node-group' : 'flow-node-card--child min-w-36',
    ]"
    :data-kind="data.kind"
    :data-block-key="data.rawData?.blockKey"
  >
    <FlowNodeHandles
      :handles="data.handles"
      target-class="!bg-neutral-500"
      target-top-class="!bg-violet-300"
    />
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="iconClass" aria-hidden="true" />
      <span v-if="isContainer" class="capitalize">{{ blockKey || data.label }}</span>
      <span v-else class="text-[11px] text-neutral-300">{{ data.label }}</span>
    </div>
  </div>
</template>
