<script setup lang="ts">
import type { BlueprintMeta } from '@mirabelle/flow-shared'
import { computed } from 'vue'
import { useNodeVisuals } from './composables/useNodeVisuals'
import type { FlowCanvasNodeProps } from './node-types'

const props = defineProps<FlowCanvasNodeProps>()
const { iconClass, stateClasses } = useNodeVisuals(() => props.data)

const meta = computed(
  () => props.data.rawData?.meta as BlueprintMeta | undefined,
)
</script>

<template>
  <div
    class="flow-node-group flow-node-card"
    :data-kind="data.kind"
    :class="stateClasses"
  >
    <div class="flex items-center gap-1.5 font-medium">
      <span class="flow-node-card__icon" :class="iconClass" aria-hidden="true" />
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
