<script setup lang="ts">
import type { BlueprintMeta } from '@mirabelle/flow-shared'
import { computed } from 'vue'
import { useFlowNodeUi } from './composables/useFlowNodeUi'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, card, title, icon } = useFlowNodeUi(() => props.data)

const meta = computed(
  () => props.data.rawData?.meta as BlueprintMeta | undefined,
)
</script>

<template>
  <div :class="card()">
    <div :class="title('flex items-center gap-1.5')">
      <span :class="icon(iconClass)" aria-hidden="true" />
      <span>Blueprint</span>
    </div>
    <div class="mt-1 text-xs font-medium text-pink-200">
      {{ data.label }}
    </div>
    <p
      v-if="meta?.description"
      class="mt-1 text-[10px] leading-snug text-neutral-400"
    >
      {{ meta.description }}
    </p>
  </div>
</template>
