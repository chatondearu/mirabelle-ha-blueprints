<script setup lang="ts">
import type { FlowNodeKind } from '@mirabelle/flow-shared'
import { Handle, Position, type NodeProps } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<NodeProps<{
  label: string
  kind: FlowNodeKind
  highlighted?: boolean
  pathActive?: boolean
  pathDimmed?: boolean
  pathFocus?: boolean
  simulationActive?: boolean
}>>()

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
  variable: 'i-lucide-variable',
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
    blueprint_input: 'border-pink-400/80 bg-pink-950/60',
    variable: 'border-teal-500 bg-teal-950',
    root: 'border-neutral-500 bg-neutral-900',
  }
  return map[kind] ?? 'border-neutral-600 bg-neutral-900'
})

const iconClass = computed(() => KIND_ICON[props.data.kind] ?? 'i-lucide-circle')

const titleKind = computed(() => {
  if (props.data.kind.startsWith('blueprint_')) {
    return props.data.kind.replace('blueprint_', '')
  }
  return props.data.kind
})

const neonClass = computed(() => {
  if (!props.data.pathActive) {
    return ''
  }
  const kind = props.data.kind
  if (kind === 'trigger') {
    return 'flow-node-neon flow-node-neon-amber'
  }
  if (kind === 'condition') {
    return 'flow-node-neon flow-node-neon-blue'
  }
  if (kind === 'variable') {
    return 'flow-node-neon flow-node-neon-teal'
  }
  if (kind === 'blueprint_meta' || kind === 'blueprint_input') {
    return 'flow-node-neon flow-node-neon-pink'
  }
  return 'flow-node-neon flow-node-neon-emerald'
})
</script>

<template>
  <div
    class="min-w-40 rounded-lg border-2 px-3 py-2 text-sm shadow-lg transition-all duration-200"
    :class="[
      colorClass,
      neonClass,
      data.pathDimmed ? 'opacity-20 saturate-50' : '',
      data.simulationActive ? 'ring-2 ring-emerald-300/80 ring-offset-2 ring-offset-neutral-950' : '',
      data.pathFocus ? 'ring-2 ring-white/50 ring-offset-2 ring-offset-neutral-950' : '',
      data.highlighted && !data.pathActive ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-neutral-950' : '',
    ]"
  >
    <Handle type="target" :position="Position.Left" class="!bg-neutral-400" />
    <div class="flex items-center gap-1.5 font-medium capitalize">
      <span
        class="size-4 shrink-0 opacity-90"
        :class="iconClass"
        aria-hidden="true"
      />
      <span>{{ titleKind }}</span>
    </div>
    <div class="mt-1 text-xs text-neutral-300">
      {{ data.label }}
    </div>
    <Handle type="source" :position="Position.Right" class="!bg-neutral-400" />
  </div>
</template>

<style scoped>
.flow-node-neon {
  box-shadow:
    0 0 10px var(--neon-color, rgba(52, 211, 153, 0.7)),
    0 0 22px var(--neon-glow, rgba(52, 211, 153, 0.35));
}
.flow-node-neon-emerald {
  --neon-color: rgba(52, 211, 153, 0.85);
  --neon-glow: rgba(52, 211, 153, 0.4);
}
.flow-node-neon-amber {
  --neon-color: rgba(251, 191, 36, 0.9);
  --neon-glow: rgba(251, 191, 36, 0.45);
}
.flow-node-neon-blue {
  --neon-color: rgba(96, 165, 250, 0.9);
  --neon-glow: rgba(96, 165, 250, 0.45);
}
.flow-node-neon-pink {
  --neon-color: rgba(244, 114, 182, 0.9);
  --neon-glow: rgba(244, 114, 182, 0.45);
}
.flow-node-neon-teal {
  --neon-color: rgba(45, 212, 191, 0.9);
  --neon-glow: rgba(45, 212, 191, 0.45);
}
</style>
