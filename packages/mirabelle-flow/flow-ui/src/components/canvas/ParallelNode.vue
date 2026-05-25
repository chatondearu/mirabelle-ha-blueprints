<script setup lang="ts">
import type { FlowCanvasNodeProps } from './node-types'
import HaContainerNode from './HaContainerNode.vue'

defineProps<FlowCanvasNodeProps>()
</script>

<template>
  <HaContainerNode v-bind="$props" />
</template>
