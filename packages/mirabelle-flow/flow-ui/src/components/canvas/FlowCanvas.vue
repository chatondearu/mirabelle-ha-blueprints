<script setup lang="ts">
import type { FlowNode as FlowNodeType } from '@mirabelle/flow-shared'
import { isConfigLayerNode } from '@mirabelle/flow-shared'
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
import { reconcileGroupLayouts } from '@mirabelle/flow-core'
import { computed, watch } from 'vue'
import { useFlowStore } from '@/stores/flow'
import {
  buildChildIdsByParent,
  computeNodeHandleVisibility,
} from './composables/node-handle-visibility'
import CanvasVariablesToolbar from './CanvasVariablesToolbar.vue'
import FlowNeonEdge from './FlowNeonEdge.vue'
import { FLOW_NODE_RENDERER_MAP } from './flow-node-renderer-map'

const store = useFlowStore()
const nodeTypes = FLOW_NODE_RENDERER_MAP as NodeTypesObject
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

const groupLayout = computed(() => {
  const doc = store.document
  if (!doc) {
    return { layout: {} as Record<string, { x: number, y: number }>, groupSizes: {} as Record<string, { width: number, height: number }> }
  }
  return reconcileGroupLayouts(
    doc.nodes,
    doc.layout,
    n => store.isNodeVisibleOnCanvas(n),
  )
})

const nodes = computed<Node[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  const { layout: layoutPositions, groupSizes } = groupLayout.value
  const childIdsByParent = buildChildIdsByParent(doc.nodes)
  return doc.nodes
    .filter(n => isNodeVisible(n.id))
    .filter(n => store.isNodeVisibleOnCanvas(n))
    .map((n: FlowNodeType) => {
      const pathActive = store.pathHighlightNodeIds.has(n.id)
      const pathDimmed =
        hasPathHighlight.value
        && !pathActive
        && !isConfigLayerNode(n)
      const simulationActive = store.simulationActiveNodeIds.has(n.id)
      const groupSize =
        groupSizes[n.id]
        ?? (n.data.groupSize as { width: number, height: number } | undefined)
      const isChild = Boolean(n.parentId)
      const isContainer = n.data.isContainer === true || n.data.isGroup === true
      return {
        id: n.id,
        type: n.kind,
        position: layoutPositions[n.id] ?? doc.layout[n.id] ?? { x: 0, y: 0 },
        parentNode: n.parentId,
        extent: n.parentId ? ('parent' as const) : undefined,
        draggable: !isChild,
        selectable: true,
        style: groupSize
          ? { width: `${groupSize.width}px`, height: `${groupSize.height}px` }
          : undefined,
        data: {
          nodeId: n.id,
          label: n.label,
          kind: n.kind,
          rawData: n.data,
          highlightedItems: store.highlightedItemsByNode[n.id] ?? [],
          highlighted: store.highlightedNodeIds.has(n.id),
          pathActive,
          pathDimmed,
          pathFocus: store.selectedNodeId === n.id,
          simulationActive,
          handles: computeNodeHandleVisibility(
            n.id,
            n.kind,
            n.parentId,
            isContainer,
            doc.edges,
            childIdsByParent,
          ),
        },
      }
    })
})

const edges = computed<Edge[]>(() => {
  const doc = store.document
  if (!doc) {
    return []
  }
  const visibleIds = new Set(
    doc.nodes.filter(n => store.isNodeVisibleOnCanvas(n)).map(n => n.id),
  )
  const selectedId = store.selectedNodeId
  return doc.edges
    .filter(e => isNodeVisible(e.source) && isNodeVisible(e.target))
    .filter(e => visibleIds.has(e.source) && visibleIds.has(e.target))
    .filter(
      e =>
        e.edgeKind !== 'reference'
        || (selectedId !== null && e.target === selectedId),
    )
    .map((e) => {
      const pathActive = store.pathHighlightEdgeIds.has(e.id)
      const traceHighlight = store.highlightedNodeIds.has(e.target)
      return {
        id: e.id,
        type: 'neon',
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
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
    if (change.type !== 'position' || !change.position || !change.id) {
      continue
    }
    const irNode = store.document?.nodes.find(n => n.id === change.id)
    if (irNode?.parentId) {
      continue
    }
    store.updateLayout(change.id, change.position.x, change.position.y)
  }
})

watch(
  () => [
    store.document?.nodes.length,
    store.pathFilterNodeId,
    store.variableFilterMode,
  ],
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

    <CanvasVariablesToolbar />

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

/* Vue Flow theme paints a white card on .vue-flow__node — hide it so .flow-node-card colors show */
.mirabelle-flow-canvas .vue-flow__node,
.mirabelle-flow-canvas .vue-flow__node-default,
.mirabelle-flow-canvas .vue-flow__node.selectable,
.mirabelle-flow-canvas .vue-flow__node.selected {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  box-shadow: none !important;
  width: auto !important;
  min-width: 0 !important;
}
</style>
