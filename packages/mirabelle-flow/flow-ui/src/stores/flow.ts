import type { TraceOverlay } from '@mirabelle/flow-shared'
import { flowDocumentSchema } from '@mirabelle/flow-shared'
import {
  getFocusedPath,
  getUpstreamPath,
  parseAutomationYaml,
  serializeDocument,
  updateNodeData,
  type MutableFlowDocument,
} from '@mirabelle/flow-core'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type AppMode = 'local' | 'ha'

export const useFlowStore = defineStore('flow', () => {
  const document = ref<MutableFlowDocument | null>(null)
  const selectedNodeId = ref<string | null>(null)
  const previewMode = ref(false)
  const previewInputs = ref<Record<string, unknown>>({})
  const parseError = ref<string | null>(null)
  const appMode = ref<AppMode>('local')
  const traceOverlay = ref<TraceOverlay | null>(null)
  const highlightedNodeIds = ref<Set<string>>(new Set())
  const pathHighlightNodeIds = ref<Set<string>>(new Set())
  const pathHighlightEdgeIds = ref<Set<string>>(new Set())
  const pathFilterNodeId = ref<string | null>(null)
  const rawYamlPanel = ref('')

  const selectedNode = computed(() =>
    document.value?.nodes.find(n => n.id === selectedNodeId.value) ?? null,
  )

  const isDirty = computed(() => document.value?._dirty ?? false)

  const pathFilterNode = computed(() =>
    document.value?.nodes.find(n => n.id === pathFilterNodeId.value) ?? null,
  )

  const pathFilterNodeIds = computed(() => {
    if (!document.value || !pathFilterNodeId.value) {
      return null
    }
    const { nodeIds } = getFocusedPath(
      pathFilterNodeId.value,
      document.value.nodes,
      document.value.edges,
    )
    return nodeIds
  })

  function applyPathHighlight(nodeIds: Set<string>, edgeIds: Set<string>) {
    pathHighlightNodeIds.value = nodeIds
    pathHighlightEdgeIds.value = edgeIds
  }

  function clearPathHighlight() {
    pathHighlightNodeIds.value = new Set()
    pathHighlightEdgeIds.value = new Set()
  }

  function loadYaml(text: string, source?: string) {
    parseError.value = null
    try {
      const doc = parseAutomationYaml(text, {
        source,
        preview: previewMode.value,
        previewInputs: previewInputs.value,
      })
      document.value = doc
      rawYamlPanel.value = text
      if (doc.blueprintMeta) {
        const defaults: Record<string, unknown> = {}
        for (const input of doc.blueprintMeta.inputs) {
          if (input.default !== undefined) {
            defaults[input.key] = input.default
          }
        }
        previewInputs.value = { ...defaults, ...previewInputs.value }
      }
      selectedNodeId.value = doc.nodes[0]?.id ?? null
      pathFilterNodeId.value = null
      clearPathHighlight()
    }
    catch (e) {
      parseError.value = e instanceof Error ? e.message : String(e)
      document.value = null
    }
  }

  function reloadWithPreview() {
    if (!document.value?.rawYaml) {
      return
    }
    loadYaml(document.value.rawYaml, document.value.source)
  }

  /** Single click: neon upstream path, show full graph. */
  function highlightNodePath(id: string) {
    if (!document.value) {
      return
    }
    selectedNodeId.value = id
    pathFilterNodeId.value = null
    const path = getUpstreamPath(id, document.value.nodes, document.value.edges)
    applyPathHighlight(path.nodeIds, path.edgeIds)
  }

  /** Double click: hide other nodes, show full parcours for this node. */
  function focusNodePath(id: string) {
    if (!document.value) {
      return
    }
    selectedNodeId.value = id
    pathFilterNodeId.value = id
    const path = getFocusedPath(id, document.value.nodes, document.value.edges)
    applyPathHighlight(path.nodeIds, path.edgeIds)
  }

  function clearPathFocus() {
    pathFilterNodeId.value = null
    clearPathHighlight()
  }

  function selectNode(id: string | null) {
    if (!id) {
      selectedNodeId.value = null
      clearPathFocus()
      return
    }
    highlightNodePath(id)
  }

  function updateLayout(nodeId: string, x: number, y: number) {
    if (!document.value) {
      return
    }
    document.value.layout[nodeId] = { x, y }
    document.value._dirty = true
  }

  function updateSelectedNodeData(data: Record<string, unknown>) {
    if (!document.value || !selectedNodeId.value) {
      return
    }
    updateNodeData(document.value, selectedNodeId.value, data)
    validateDocument()
  }

  function validateDocument(): boolean {
    if (!document.value) {
      return false
    }
    const result = flowDocumentSchema.safeParse({
      kind: document.value.kind,
      source: document.value.source,
      alias: document.value.alias,
      mode: document.value.mode,
      nodes: document.value.nodes,
      edges: document.value.edges,
      layout: document.value.layout,
    })
    return result.success
  }

  function exportYaml(): string {
    if (!document.value) {
      return ''
    }
    return serializeDocument(document.value)
  }

  function setTrace(overlay: TraceOverlay | null) {
    traceOverlay.value = overlay
    if (!overlay || !document.value) {
      highlightedNodeIds.value = new Set()
      return
    }
    const ids = new Set<string>()
    for (const step of overlay.steps) {
      const nodeId = step.path.replace(/\//g, '_')
      if (document.value.nodes.some(n => n.id === nodeId)) {
        ids.add(nodeId)
      }
      for (const node of document.value.nodes) {
        if (node.path === step.path || step.path.startsWith(`${node.path}/`)) {
          ids.add(node.id)
        }
      }
    }
    highlightedNodeIds.value = ids
  }

  return {
    document,
    selectedNodeId,
    selectedNode,
    previewMode,
    previewInputs,
    parseError,
    appMode,
    traceOverlay,
    highlightedNodeIds,
    pathHighlightNodeIds,
    pathHighlightEdgeIds,
    pathFilterNodeId,
    pathFilterNode,
    pathFilterNodeIds,
    rawYamlPanel,
    isDirty,
    loadYaml,
    reloadWithPreview,
    selectNode,
    highlightNodePath,
    focusNodePath,
    clearPathFocus,
    updateLayout,
    updateSelectedNodeData,
    validateDocument,
    exportYaml,
    setTrace,
  }
})
