<script setup lang="ts">
import type { FlowNode as FlowNodeType } from '@mirabelle/flow-shared'
import {
  VueFlow,
  useVueFlow,
  type Edge,
  type EdgeTypesObject,
  type Node,
  type NodeDragEvent,
  type NodeTypesObject,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { computed, watch } from 'vue'
import { useFlowStore } from '@/stores/flow'
import FlowNeonEdge from './FlowNeonEdge.vue'
import FlowNodeComponent from './FlowNode.vue'

const store = useFlowStore()
const nodeTypes = { flow: FlowNodeComponent } as NodeTypesObject
const edgeTypes = { neon: FlowNeonEdge } as EdgeTypesObject

const { onNodeClick, onNodeDoubleClick, onPaneClick, onNodesChange, fitView } = useVueFlow()

function isNodeVisible(nodeId: string): boolean {
  const visible = store.pathFilterNodeIds
  if (!visible) {
    return true
  }
  return visible.has(nodeId)
}

const hasPathHighlight = computed(
  () => store.pathHighlightNodeIds.size > 0 && !store.pathFilterNodeId,
)

const nodes = computed<Node[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  return doc.nodes
    .filter(n => isNodeVisible(n.id))
    .map((n: FlowNodeType) => {
      const pathActive = store.pathHighlightNodeIds.has(n.id)
      const pathDimmed = hasPathHighlight.value && !pathActive
      const simulationActive = store.simulationActiveNodeIds.has(n.id)
      return {
        id: n.id,
        type: 'flow',
        position: doc.layout[n.id] ?? { x: 0, y: 0 },
        data: {
          label: n.label,
          kind: n.kind,
          highlighted: store.highlightedNodeIds.has(n.id),
          pathActive,
          pathDimmed,
          pathFocus: store.selectedNodeId === n.id,
          simulationActive,
        },
      }
    })
})

const edges = computed<Edge[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  return doc.edges
    .filter(e => isNodeVisible(e.source) && isNodeVisible(e.target))
    .map((e) => {
      const pathActive = store.pathHighlightEdgeIds.has(e.id)
      const traceHighlight = store.highlightedNodeIds.has(e.target)
      return {
        id: e.id,
        type: 'neon',
        source: e.source,
        target: e.target,
        label: e.label,
        labelStyle: pathActive
          ? { fill: '#6ee7b7', fontSize: 10, fontWeight: 600 }
          : e.edgeKind === 'reference'
            ? { fill: '#c4b5fd', fontSize: 10 }
            : undefined,
        data: {
          active: pathActive || (traceHighlight && e.edgeKind !== 'reference'),
          edgeKind: e.edgeKind,
        },
      }
    })
})

onNodeClick(({ node }) => {
  store.highlightNodePath(node.id)
})

onNodeDoubleClick(({ node }) => {
  store.focusNodePath(node.id)
})

onPaneClick(() => {
  store.clearPathFocus()
})

onNodesChange((changes) => {
  for (const change of changes) {
    if (change.type === 'position' && change.position && change.id) {
      store.updateLayout(change.id, change.position.x, change.position.y)
    }
  }
})

watch(
  () => [store.document?.nodes.length, store.pathFilterNodeId],
  () => {
    setTimeout(() => fitView({ padding: 0.2 }), 50)
  },
)
</script>

<template>
  <div class="relative flex h-full w-full flex-col">
    <div
      v-if="store.pathFilterNode"
      class="flex shrink-0 items-center gap-2 border-b border-emerald-900/50 bg-emerald-950/40 px-3 py-1.5 text-xs text-emerald-100"
    >
      <span class="i-lucide-focus size-3.5 shrink-0 opacity-80" aria-hidden="true" />
      <span>
        Focused path:
        <strong>{{ store.pathFilterNode.label }}</strong>
        <span class="text-emerald-400/70">(double-click to focus · click canvas to reset)</span>
      </span>
      <button
        type="button"
        class="ml-auto rounded bg-neutral-800 px-2 py-0.5 text-neutral-300 hover:bg-neutral-700"
        @click="store.clearPathFocus()"
      >
        Show all
      </button>
    </div>
    <div
      v-else-if="hasPathHighlight && store.selectedNode"
      class="flex shrink-0 items-center gap-2 border-b border-emerald-900/30 bg-neutral-900/80 px-3 py-1 text-xs text-neutral-400"
    >
      <span class="i-lucide-git-branch size-3.5 text-emerald-400/80" aria-hidden="true" />
      Upstream path for <strong class="text-emerald-300">{{ store.selectedNode.label }}</strong>
      · double-click to isolate
    </div>

    <div class="relative min-h-0 flex-1">
      <VueFlow
        v-if="nodes.length"
        :nodes="nodes"
        :edges="edges"
        :node-types="nodeTypes"
        :edge-types="edgeTypes"
        class="mirabelle-flow-canvas h-full w-full"
        @node-drag-stop="(e: NodeDragEvent) => {
          if (e.node.position) {
            store.updateLayout(e.node.id, e.node.position.x, e.node.position.y)
          }
        }"
      >
        <Background pattern-color="#404040" :gap="16" />
        <Controls />
      </VueFlow>
      <div
        v-else
        class="flex h-full items-center justify-center text-neutral-500"
      >
        Open a YAML file or load a repo blueprint
      </div>
    </div>
  </div>
</template>

<style>
.mirabelle-flow-canvas {
  background: #0a0a0a;
}
</style>
