<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const visuals = useNodeVisuals(props.data)

const isContainer = computed(() => props.data.rawData?.isContainer === true)
const blockKey = computed(() => String(props.data.rawData?.blockKey ?? ''))
</script>

<template>
  <div
    class="flow-node-card"
    :class="[
      visuals.stateClasses,
      isContainer ? 'flow-node-group' : 'flow-node-card--child min-w-36',
    ]"
    :data-kind="data.kind"
  >
    <Handle
      v-if="!isContainer"
      type="target"
      :position="Position.Left"
      class="!bg-neutral-500"
    />
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="visuals.iconClass" aria-hidden="true" />
      <span v-if="isContainer" class="capitalize">{{ blockKey || data.label }}</span>
      <span v-else class="text-[11px] text-neutral-300">{{ data.label }}</span>
    </div>
    <Handle
      v-if="isContainer"
      type="target"
      :position="Position.Left"
      class="!bg-neutral-400"
    />
    <Handle
      v-if="isContainer"
      type="source"
      :position="Position.Right"
      id="flow"
      class="!bg-neutral-400"
      style="top: 50%"
    />
  </div>
</template>
