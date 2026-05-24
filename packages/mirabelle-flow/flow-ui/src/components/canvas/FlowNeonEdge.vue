<script setup lang="ts">
import { BaseEdge, getBezierPath, type EdgeProps } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<EdgeProps<{ active?: boolean, edgeKind?: string }>>()

const path = computed(() => getBezierPath(props))

const pathD = computed(() => path.value[0])

const strokeColor = computed(() =>
  props.data?.edgeKind === 'reference' ? '#c4b5fd' : '#34d399',
)

const markerId = computed(() => {
  const suffix = props.data?.edgeKind === 'reference' ? 'ref' : 'flow'
  return `neon-arrow-${suffix}-${props.id}`
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
      :marker-end="`url(#${markerId})`"
      :style="{
        stroke: data?.active ? strokeColor : '#404040',
        strokeWidth: data?.active ? 2.5 : 1.5,
        opacity: data?.active ? 1 : 0.3,
      }"
    />

    <template v-if="data?.active">
      <BaseEdge
        :path="pathD"
        :style="{
          stroke: strokeColor,
          strokeWidth: 5,
          opacity: 0.35,
          filter: `drop-shadow(0 0 6px ${strokeColor})`,
        }"
      />
      <circle r="3.5" :fill="strokeColor" opacity="0.95">
        <animateMotion
          dur="1.8s"
          repeatCount="indefinite"
          :path="pathD"
        />
      </circle>
      <circle r="1.5" fill="#ecfdf5" opacity="0.9">
        <animateMotion
          dur="1.8s"
          repeatCount="indefinite"
          :path="pathD"
        />
      </circle>
    </template>
  </g>
</template>
