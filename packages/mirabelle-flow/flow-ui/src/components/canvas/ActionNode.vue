<script setup lang="ts">
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, stateClasses } = useNodeVisuals(() => props.data)

const service = computed(() =>
  typeof props.data.rawData?.service === 'string'
    ? props.data.rawData.service
    : null,
)

const subtitle = computed(() => {
  const label = props.data.label
  if (!service.value || label === service.value) {
    return null
  }
  return label
})
</script>

<template>
  <div
    class="flow-node-card"
    :data-kind="data.kind"
    :class="stateClasses"
  >
    <FlowNodeHandles :handles="data.handles" />
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="iconClass" aria-hidden="true" />
      <span class="text-emerald-300">{{ service ?? data.label }}</span>
    </div>
    <div v-if="subtitle" class="mt-1 text-[10px] leading-snug text-neutral-400">
      {{ subtitle }}
    </div>
  </div>
</template>
