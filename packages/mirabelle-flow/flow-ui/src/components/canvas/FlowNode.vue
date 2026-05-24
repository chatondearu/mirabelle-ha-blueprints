<script setup lang="ts">
import type { FlowNodeKind } from '@mirabelle/flow-shared'
import { Handle, Position, type NodeProps } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<NodeProps<{ label: string, kind: FlowNodeKind, highlighted?: boolean }>>()

/** Lucide icons via UnoCSS preset-icons (`i-lucide-*`). */
const KIND_ICON: Record<FlowNodeKind, string> = {
  trigger: 'i-lucide-zap',
  condition: 'i-lucide-filter',
  action: 'i-lucide-play',
  choose: 'i-lucide-git-branch',
  sequence: 'i-lucide-list-ordered',
  parallel: 'i-lucide-layers',
  repeat: 'i-lucide-repeat',
  delay: 'i-lucide-clock',
  wait: 'i-lucide-hourglass',
  variables: 'i-lucide-braces',
  blueprint_input: 'i-lucide-sliders-horizontal',
  blueprint_meta: 'i-lucide-file-code-2',
  root: 'i-lucide-workflow',
}

const colorClass = computed(() => {
  const kind = props.data.kind
  const map: Record<string, string> = {
    trigger: 'border-amber-500 bg-amber-950',
    condition: 'border-blue-500 bg-blue-950',
    action: 'border-emerald-500 bg-emerald-950',
    choose: 'border-purple-500 bg-purple-950',
    variables: 'border-cyan-500 bg-cyan-950',
    blueprint_meta: 'border-pink-500 bg-pink-950',
    root: 'border-neutral-500 bg-neutral-900',
  }
  return map[kind] ?? 'border-neutral-600 bg-neutral-900'
})

const iconClass = computed(() => KIND_ICON[props.data.kind] ?? 'i-lucide-circle')
</script>

<template>
  <div
    class="min-w-40 rounded-lg border-2 px-3 py-2 text-sm shadow-lg transition-all"
    :class="[
      colorClass,
      data.highlighted ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-neutral-950' : '',
    ]"
  >
    <Handle type="target" :position="Position.Left" class="!bg-neutral-400" />
    <div class="flex items-center gap-1.5 font-medium capitalize">
      <span
        class="size-4 shrink-0 opacity-90"
        :class="iconClass"
        aria-hidden="true"
      />
      <span>{{ data.kind }}</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
    <Handle type="source" :position="Position.Right" class="!bg-neutral-400" />
  </div>
</template>
