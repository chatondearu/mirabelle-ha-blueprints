<script setup lang="ts">
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from 'reka-ui'
import { onMounted, ref } from 'vue'
import { useYamlIO } from '@/composables/useYamlIO'
import { listRepoBlueprints, loadRepoBlueprint } from '@/data/repo-blueprints'
import SimulationCatalogPanel from '@/components/inspector/SimulationCatalogPanel.vue'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const { openFile, loadText } = useYamlIO()
const repoFiles = ref<{ path: string, name: string }[]>([])
const pasteYaml = ref('')

onMounted(async () => {
  repoFiles.value = await listRepoBlueprints()
})

async function loadRepo(path: string) {
  const yaml = await loadRepoBlueprint(path)
  const name = path.split('/').pop()
  store.loadYaml(yaml, name)
}

function applyPaste() {
  if (pasteYaml.value.trim()) {
    loadText(pasteYaml.value, 'pasted.yaml')
  }
}
</script>

<template>
  <TabsRoot default-value="repo" class="flex h-full flex-col">
    <TabsList class="flex border-b border-neutral-800">
      <TabsTrigger
        value="repo"
        class="flex-1 px-2 py-2 text-xs data-[state=active]:border-b-2 data-[state=active]:border-emerald-500"
      >
        Repo
      </TabsTrigger>
      <TabsTrigger
        value="file"
        class="flex-1 px-2 py-2 text-xs data-[state=active]:border-b-2 data-[state=active]:border-emerald-500"
      >
        File
      </TabsTrigger>
      <TabsTrigger
        value="paste"
        class="flex-1 px-2 py-2 text-xs data-[state=active]:border-b-2 data-[state=active]:border-emerald-500"
      >
        Paste
      </TabsTrigger>
    </TabsList>

    <TabsContent value="repo" class="flex-1 overflow-y-auto p-2">
      <button
        class="mb-2 w-full rounded bg-emerald-800 px-2 py-1 text-xs hover:bg-emerald-700"
        type="button"
        @click="openFile"
      >
        Open local file…
      </button>
      <ul class="space-y-1">
        <li v-for="file in repoFiles" :key="file.path">
          <button
            type="button"
            class="w-full truncate rounded px-2 py-1 text-left text-xs hover:bg-neutral-800"
            :title="file.path"
            @click="loadRepo(file.path)"
          >
            {{ file.name }}
          </button>
        </li>
      </ul>
    </TabsContent>

    <TabsContent value="file" class="p-2">
      <button
        type="button"
        class="w-full rounded bg-neutral-800 px-3 py-2 text-sm hover:bg-neutral-700"
        @click="openFile"
      >
        Choose YAML file
      </button>
    </TabsContent>

    <TabsContent value="paste" class="flex flex-1 flex-col gap-2 p-2">
      <textarea
        v-model="pasteYaml"
        class="min-h-32 flex-1 rounded border border-neutral-700 bg-neutral-900 p-2 font-mono text-xs"
        placeholder="Paste automation YAML…"
      />
      <button
        type="button"
        class="rounded bg-emerald-800 px-3 py-1 text-sm hover:bg-emerald-700"
        @click="applyPaste"
      >
        Load
      </button>
    </TabsContent>
    <SimulationCatalogPanel />
  </TabsRoot>
</template>
