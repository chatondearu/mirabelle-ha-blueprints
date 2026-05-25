<script setup lang="ts">
import { computed, onMounted } from 'vue'
import FlowCanvas from '@/components/canvas/FlowCanvas.vue'
import NodeInspector from '@/components/inspector/NodeInspector.vue'
import FileExplorer from '@/components/sidebar/FileExplorer.vue'
import HaEntityList from '@/components/sidebar/HaEntityList.vue'
import TraceTimeline from '@/components/trace/TraceTimeline.vue'
import { useYamlIO } from '@/composables/useYamlIO'
import { useHaConnection } from '@/composables/useHaConnection'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const { downloadYaml } = useYamlIO()
const ha = useHaConnection()

const isHaPanel = computed(
  () => typeof window !== 'undefined' && (window.location.pathname.includes('mirabelle-flow') || window.hassUrl),
)

onMounted(async () => {
  if (isHaPanel.value) {
    store.appMode = 'ha'
    await ha.connect()
  }
})

async function saveToHa() {
  if (!store.document?.source?.startsWith('automation:')) {
    return
  }
  const id = store.document.source.replace('automation:', '')
  const yaml = store.exportYaml()
  const { parse } = await import('yaml')
  const config = parse(yaml) as Record<string, unknown>
  await ha.updateAutomation(id, config)
  if (store.document.layout) {
    await ha.saveLayout(store.document.source, store.document.layout)
  }
}
</script>

<template>
  <div class="flex h-screen flex-col">
      <header class="flex items-center gap-3 border-b border-neutral-800 px-4 py-2">
        <h1 class="text-lg font-semibold text-emerald-400">
          Mirabelle Flow
        </h1>
        <div class="flex gap-1 rounded bg-neutral-900 p-0.5 text-xs">
          <button
            type="button"
            class="rounded px-2 py-1"
            :class="store.appMode === 'local' ? 'bg-neutral-700' : ''"
            @click="store.appMode = 'local'"
          >
            Local files
          </button>
          <button
            type="button"
            class="rounded px-2 py-1"
            :class="store.appMode === 'ha' ? 'bg-neutral-700' : ''"
            :disabled="!isHaPanel && !ha.connected.value"
            @click="store.appMode = 'ha'"
          >
            Home Assistant
          </button>
        </div>
        <span v-if="store.document" class="text-sm text-neutral-400">
          {{ store.document.blueprintMeta?.name ?? store.document.source ?? 'Untitled' }}
          <span v-if="store.isDirty" class="text-amber-400">•</span>
        </span>
        <div
          v-if="store.document?.kind === 'blueprint'"
          class="flex items-center gap-1 rounded bg-neutral-900 p-0.5 text-xs"
        >
          <button
            type="button"
            class="rounded px-2 py-1"
            :class="store.viewMode === 'split' ? 'bg-neutral-700' : ''"
            @click="store.setViewMode('split')"
          >
            Inputs + Variables
          </button>
          <button
            type="button"
            class="rounded px-2 py-1"
            :class="store.viewMode === 'combined' ? 'bg-neutral-700' : ''"
            @click="store.setViewMode('combined')"
          >
            Combined
          </button>
        </div>
        <div class="ml-auto flex gap-2">
          <button
            type="button"
            class="rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700"
            :disabled="!store.document"
            @click="downloadYaml"
          >
            Export YAML
          </button>
          <button
            v-if="store.appMode === 'ha'"
            type="button"
            class="rounded bg-emerald-800 px-3 py-1 text-sm hover:bg-emerald-700"
            :disabled="!store.document"
            @click="saveToHa"
          >
            Save to HA
          </button>
        </div>
      </header>

      <p v-if="store.parseError" class="bg-red-950 px-4 py-2 text-sm text-red-300">
        {{ store.parseError }}
      </p>

      <div class="flex min-h-0 flex-1">
        <aside class="w-56 shrink-0 border-r border-neutral-800 overflow-hidden flex flex-col">
          <FileExplorer v-if="store.appMode === 'local'" />
          <HaEntityList v-else />
        </aside>

        <main class="flex min-w-0 flex-1 flex-col">
          <div class="min-h-0 flex-1">
            <FlowCanvas />
          </div>
          <div class="h-36 shrink-0">
            <TraceTimeline />
          </div>
        </main>

        <aside class="w-72 shrink-0 border-l border-neutral-800 overflow-hidden">
          <NodeInspector />
        </aside>
      </div>
  </div>
</template>
