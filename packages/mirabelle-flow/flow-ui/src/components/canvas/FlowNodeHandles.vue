<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { NodeHandleVisibility } from './composables/node-handle-visibility'

defineProps<{
  handles: NodeHandleVisibility
  sourceId?: string
  targetClass?: string
  sourceClass?: string
}>()
</script>

<template>
  <Handle
    v-if="handles.showTarget"
    type="target"
    :position="Position.Left"
    :class="targetClass ?? '!bg-neutral-400'"
  />
  <Handle
    v-if="handles.showSource"
    type="source"
    :position="Position.Right"
    :id="sourceId"
    :class="sourceClass ?? '!bg-neutral-400'"
  />
</template>
