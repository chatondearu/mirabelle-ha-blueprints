<script setup lang="ts">
import type { VariableFilterMode } from '@mirabelle/flow-shared'
import { computed } from 'vue'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()

const stats = computed(() => store.variableFilterStats)

const modes: { id: VariableFilterMode, label: string, title: string }[] = [
  {
    id: 'binding_only',
    label: 'Used in flow',
    title: 'Show variables referenced outside the variables group',
  },
  {
    id: 'all',
    label: 'All variables',
    title: 'Show every blueprint variable, including internal aliases',
  },
]

function isActive(mode: VariableFilterMode): boolean {
  return store.variableFilterMode === mode
}
</script>

<template>
  <div
    v-if="store.hasBlueprintVariables"
    class="flex shrink-0 flex-wrap items-center gap-2 border-b border-cyan-900/40 bg-cyan-950/25 px-3 py-1.5 text-xs text-cyan-100"
  >
    <span class="i-lucide-braces size-3.5 shrink-0 text-cyan-400/80" aria-hidden="true" />
    <span class="font-medium text-cyan-200/90">
      Variables
    </span>
    <div class="flex gap-0.5 rounded bg-neutral-900/80 p-0.5">
      <button
        v-for="mode in modes"
        :key="mode.id"
        type="button"
        class="rounded px-2 py-0.5 transition-colors"
        :class="isActive(mode.id) ? 'bg-cyan-900/70 text-cyan-100' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'"
        :title="mode.title"
        @click="store.setVariableFilterMode(mode.id)"
      >
        {{ mode.label }}
      </button>
    </div>
    <span
      v-if="stats.hidden > 0 && store.variableFilterMode === 'binding_only'"
      class="text-neutral-500"
    >
      {{ stats.hidden }} internal hidden
    </span>
    <span
      v-else-if="store.variableFilterMode === 'all' && stats.hidden > 0"
      class="text-neutral-500"
    >
      {{ stats.total }} total
    </span>
  </div>
</template>
