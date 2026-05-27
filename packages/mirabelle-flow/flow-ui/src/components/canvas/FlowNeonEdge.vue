<script setup lang="ts">
import { BaseEdge, getBezierPath, type EdgeProps } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<EdgeProps<{ active?: boolean, edgeKind?: string }>>()

const path = computed(() => getBezierPath(props))

const pathD = computed(() => path.value[0])

const strokeColor = computed(() => {
  switch (props.data?.edgeKind) {
    case 'reference':
      return '#c4b5fd'
    case 'input_binding':
      return '#22d3ee'
    case 'variable_binding':
      return '#2dd4bf'
    default:
      return '#34d399'
  }
})

const isBinding = computed(() =>
  props.data?.edgeKind === 'input_binding'
  || props.data?.edgeKind === 'variable_binding'
  || props.data?.edgeKind === 'reference',
)

const markerId = computed(() => {
  const kind = props.data?.edgeKind ?? 'flow'
  return `neon-arrow-${kind}-${props.id}`
})
</script>

<template>
  <g class="flow-neon-edge">
    <defs>
      <marker
        :id="markerId"
        markerWidth="8"
        markerHeight="8"
        refX="7"
        refY="4"
        orient="auto"
        markerUnits="strokeWidth"
      >
        <path
          d="M0,0 L8,4 L0,8 Z"
          :fill="data?.active ? strokeColor : '#525252'"
        />
      </marker>
    </defs>

    <BaseEdge
      :id="id"
      :path="pathD"
      :marker-end="isBinding ? undefined : `url(#${markerId})`"
      :style="{
        stroke: data?.active ? strokeColor : '#404040',
        strokeWidth: data?.active ? 2.5 : 1.5,
        opacity: data?.active ? 1 : isBinding ? 0.45 : 0.3,
        strokeDasharray: isBinding ? '6 4' : undefined,
      }"
    />

    <template v-if="data?.active">
      <BaseEdge
        :path="pathD"
        :style="{
          stroke: strokeColor,
          strokeWidth: isBinding ? 4 : 5,
          opacity: 0.35,
          filter: `drop-shadow(0 0 6px ${strokeColor})`,
        }"
      />
      <circle v-if="!isBinding" r="3.5" :fill="strokeColor" opacity="0.95">
        <animateMotion dur="1.8s" repeatCount="indefinite" :path="pathD" />
      </circle>
      <circle v-if="isBinding" r="2.5" :fill="strokeColor" opacity="0.9">
        <animateMotion dur="2.2s" repeatCount="indefinite" :path="pathD" />
      </circle>
    </template>
  </g>
</template>
