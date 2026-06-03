<script setup lang="ts">
import { computed } from 'vue'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import FlowNodeHandles from './FlowNodeHandles.vue'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, card, title, label, icon } = useFlowNodeUi(() => props.data)

const service = computed(() =>
  typeof props.data.rawData?.service === 'string'
    ? props.data.rawData.service
    : null,
)

const subtitle = computed(() => {
  const labelText = props.data.label
  if (!service.value || labelText === service.value) {
    return null
  }
  return labelText
})
</script>

<template>
  <div :class="card()">
    <FlowNodeHandles :handles="data.handles" />
    <div :class="title('flex items-center gap-1.5')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span class="text-emerald-300">{{ service ?? data.label }}</span>
    </div>
    <div
      v-if="subtitle"
      :class="label('mt-1 text-[10px] leading-snug text-neutral-400')"
    >
      {{ subtitle }}
    </div>
  </div>
</template>
