<script setup lang="ts">
import type { FlowNode as FlowNodeType } from '@mirabelle/flow-shared'
import {
  VueFlow,
  useVueFlow,
  type Edge,
  type Node,
  type NodeDragEvent,
  type NodeTypesObject,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { computed, watch } from 'vue'
import { useFlowStore } from '@/stores/flow'
import FlowNodeComponent from './FlowNode.vue'

const store = useFlowStore()
const nodeTypes = { flow: FlowNodeComponent } as NodeTypesObject

const { onNodeClick, onNodesChange, fitView } = useVueFlow()

const nodes = computed<Node[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  return doc.nodes.map((n: FlowNodeType) => ({
    id: n.id,
    type: 'flow',
    position: doc.layout[n.id] ?? { x: 0, y: 0 },
    data: {
      label: n.label,
      kind: n.kind,
      highlighted: store.highlightedNodeIds.has(n.id),
    },
  }))
})

const edges = computed<Edge[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  return doc.edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: store.highlightedNodeIds.has(e.target),
    style: store.highlightedNodeIds.has(e.target)
      ? { stroke: '#facc15', strokeWidth: 2 }
      : undefined,
  }))
})

onNodeClick(({ node }) => {
  store.selectNode(node.id)
})

onNodesChange((changes) => {
  for (const change of changes) {
    if (change.type === 'position' && change.position && change.id) {
      store.updateLayout(change.id, change.position.x, change.position.y)
    }
  }
})

watch(
  () => store.document?.nodes.length,
  () => {
    setTimeout(() => fitView({ padding: 0.2 }), 50)
  },
)
</script>

<template>
  <div class="h-full w-full">
    <VueFlow
      v-if="nodes.length"
      :nodes="nodes"
      :edges="edges"
      :node-types="nodeTypes"
      class="mirabelle-flow-canvas"
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
</template>

<style>
.mirabelle-flow-canvas {
  background: #0a0a0a;
}
</style>
