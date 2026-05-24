<script setup lang="ts">
import { computed } from 'vue'
import { useFlowStore } from '@/stores/flow'

const store = useFlowStore()

const node = computed(() => store.selectedNode)

const varName = computed(() =>
  node.value?.path.replace(/^variables\//, '') ?? '',
)

const consumers = computed(() => {
  if (!node.value || !store.document) {
    return []
  }
  return store.document.edges
    .filter(
      e =>
        e.edgeKind === 'variable_binding'
        && e.source === node.value!.id,
    )
    .map((e) => {
      const target = store.document!.nodes.find(n => n.id === e.target)
      return { edge: e, node: target }
    })
    .filter(x => x.node)
})
</script>

<template>
  <div v-if="node" class="flex flex-col gap-4 overflow-y-auto p-4">
    <div>
      <div class="text-xs text-neutral-500">
        variable · {{ node.path }}
      </div>
      <h2 class="text-lg font-semibold text-cyan-300">
        {{ varName }}
      </h2>
    </div>

    <div class="rounded border border-cyan-900/40 bg-cyan-950/30 p-3 text-xs">
      <div class="text-neutral-400">
        YAML value
      </div>
      <pre class="mt-1 whitespace-pre-wrap font-mono text-cyan-100">{{ JSON.stringify(node.data.value ?? node.data, null, 2) }}</pre>
    </div>

    <div>
      <h3 class="mb-2 text-sm font-medium">
        Used by
      </h3>
      <ul v-if="consumers.length" class="space-y-1">
        <li
          v-for="item in consumers"
          :key="item.edge.id"
        >
          <button
            type="button"
            class="w-full rounded bg-neutral-800 px-2 py-1 text-left text-xs hover:bg-neutral-700"
            @click="store.highlightNodePath(item.node!.id)"
          >
            {{ item.node!.label }}
            <span class="text-neutral-500">({{ item.node!.kind }})</span>
          </button>
        </li>
      </ul>
      <p v-else class="text-xs text-neutral-500">
        No static references detected in templates.
      </p>
      <button
        type="button"
        class="mt-2 text-xs text-cyan-400 hover:underline"
        @click="store.highlightVariableBindings(node.id)"
      >
        Highlight bindings on graph
      </button>
    </div>
  </div>
</template>
