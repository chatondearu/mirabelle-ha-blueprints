<script setup lang="ts">
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import FlowNodeHandles from './FlowNodeHandles.vue'
import IfContainerNode from './IfContainerNode.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, stateClasses } = useNodeVisuals(() => props.data)

const isContainer = computed(() => props.data.rawData?.isContainer === true)
const isIfContainer = computed(
  () => isContainer.value && props.data.rawData?.blockKey === 'if',
)
const blockKey = computed(() => String(props.data.rawData?.blockKey ?? ''))
</script>

<template>
  <IfContainerNode v-if="isIfContainer" v-bind="props" />
  <div
    v-else
    class="flow-node-card"
    :class="[
      stateClasses,
      isContainer ? 'flow-node-group' : 'flow-node-card--child min-w-36',
    ]"
    :data-kind="data.kind"
  >
    <FlowNodeHandles v-if="!isContainer" :handles="data.handles" target-class="!bg-neutral-500" />
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="iconClass" aria-hidden="true" />
      <span v-if="isContainer" class="capitalize">{{ blockKey || data.label }}</span>
      <span v-else class="text-[11px] text-neutral-300">{{ data.label }}</span>
    </div>
  </div>
</template>
