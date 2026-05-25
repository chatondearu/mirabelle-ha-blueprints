<script setup lang="ts">
import type { FlowCanvasNodeProps } from './node-types'
import StandardNode from './StandardNode.vue'

defineProps<FlowCanvasNodeProps>()
</script>

<template>
  <StandardNode v-bind="$props" />
</template>

