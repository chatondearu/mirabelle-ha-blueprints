<script setup lang="ts">
import { Label } from 'reka-ui'
import { computed, ref, watch } from 'vue'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()
const serviceField = ref('')
const entityField = ref('')
const rawJson = ref('')

const node = computed(() => store.selectedNode)

watch(
  node,
  (n) => {
    if (!n) {
      return
    }
    serviceField.value = typeof n.data.service === 'string' ? n.data.service : ''
    const target = n.data.target as { entity_id?: string } | undefined
    entityField.value = typeof target?.entity_id === 'string' ? target.entity_id : ''
    rawJson.value = JSON.stringify(n.data, null, 2)
  },
  { immediate: true },
)

function applyService() {
  if (!node.value) {
    return
  }
  const data = { ...node.value.data, service: serviceField.value }
  store.updateSelectedNodeData(data)
}

function applyEntity() {
  if (!node.value) {
    return
  }
  const data = {
    ...node.value.data,
    target: { entity_id: entityField.value },
  }
  store.updateSelectedNodeData(data)
}

function applyRaw() {
  try {
    const data = JSON.parse(rawJson.value) as Record<string, unknown>
    store.updateSelectedNodeData(data)
  }
  catch {
    // invalid JSON
  }
}

function setPreviewInput(key: string, value: string) {
  store.previewInputs[key] = value
  store.reloadWithPreview()
}
</script>

<template>
  <div v-if="!node" class="p-4 text-sm text-neutral-500">
    Select a node
  </div>
  <div v-else class="flex flex-col gap-4 overflow-y-auto p-4">
    <div>
      <div class="text-xs text-neutral-500">
        {{ node.kind }} · {{ node.path }}
      </div>
      <h2 class="text-lg font-semibold">
        {{ node.label }}
      </h2>
    </div>

    <template v-if="node.kind === 'action'">
      <div>
        <Label class="text-xs text-neutral-400">Service</Label>
        <input
          v-model="serviceField"
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
          @change="applyService"
        >
      </div>
      <div>
        <Label class="text-xs text-neutral-400">Target entity_id</Label>
        <input
          v-model="entityField"
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
          @change="applyEntity"
        >
      </div>
    </template>

    <div v-if="store.document?.blueprintMeta">
      <h3 class="mb-2 text-sm font-medium">
        Blueprint preview inputs
      </h3>
      <label class="mb-2 flex items-center gap-2 text-xs">
        <input
          v-model="store.previewMode"
          type="checkbox"
          @change="store.reloadWithPreview()"
        >
        Preview mode
      </label>
      <div
        v-for="input in store.document.blueprintMeta.inputs"
        :key="input.key"
        class="mb-2"
      >
        <Label class="text-xs">{{ input.name ?? input.key }}</Label>
        <input
          :value="String(store.previewInputs[input.key] ?? input.default ?? '')"
          class="mt-1 w-full rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs"
          @change="(e) => setPreviewInput(input.key, (e.target as HTMLInputElement).value)"
        >
      </div>
    </div>

    <div>
      <Label class="text-xs text-neutral-400">Raw node data (JSON)</Label>
      <textarea
        v-model="rawJson"
        class="mt-1 h-40 w-full rounded border border-neutral-700 bg-neutral-900 p-2 font-mono text-xs"
      />
      <button
        type="button"
        class="mt-1 rounded bg-neutral-700 px-2 py-1 text-xs"
        @click="applyRaw"
      >
        Apply JSON
      </button>
    </div>
  </div>
</template>
