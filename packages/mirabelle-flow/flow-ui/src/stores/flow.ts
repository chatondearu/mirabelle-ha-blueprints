import type { SimulationCatalog, TraceOverlay } from '@mirabelle/flow-shared'
import {
  loadSimulationCatalog,
  saveSimulationCatalog,
} from '@mirabelle/flow-shared'
import { flowDocumentSchema } from '@mirabelle/flow-shared'
import {
  getBindingHighlight,
  getFocusedPath,
  getSimulationActiveNodeIds,
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
  const previewMode = ref(true)
  const previewInputs = ref<Record<string, unknown>>({})
  const simulationCatalog = ref<SimulationCatalog>(loadSimulationCatalog())
  const parseError = ref<string | null>(null)
  const appMode = ref<AppMode>('local')
  const traceOverlay = ref<TraceOverlay | null>(null)
  const highlightedNodeIds = ref<Set<string>>(new Set())
  const pathHighlightNodeIds = ref<Set<string>>(new Set())
  const pathHighlightEdgeIds = ref<Set<string>>(new Set())
  const pathFilterNodeId = ref<string | null>(null)
  const simulationActiveNodeIds = ref<Set<string>>(new Set())
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

  function updateSimulationActiveForTrigger(triggerId: string | null) {
    if (
      !document.value
      || !previewMode.value
      || !triggerId
    ) {
      simulationActiveNodeIds.value = new Set()
      return
    }
    const trigger = document.value.nodes.find(
      n => n.id === triggerId && n.kind === 'trigger',
    )
    if (!trigger) {
      simulationActiveNodeIds.value = new Set()
      return
    }
    simulationActiveNodeIds.value = getSimulationActiveNodeIds(
      triggerId,
      document.value.nodes,
      document.value.edges,
    )
  }

  function loadYaml(text: string, source?: string) {
    parseError.value = null
    try {
      const doc = parseAutomationYaml(text, {
        source,
        preview: previewMode.value,
        previewInputs: previewInputs.value,
        simulationCatalog: simulationCatalog.value,
      })
      document.value = doc
      rawYamlPanel.value = text
      const meta = doc.nodes.find(n => n.kind === 'blueprint_meta')
      const sim = meta?.data.simulationValues as Record<string, unknown> | undefined
      if (sim) {
        previewInputs.value = { ...sim }
      }
      else if (doc.blueprintMeta) {
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
      updateSimulationActiveForTrigger(
        selectedNode.value?.kind === 'trigger' ? selectedNodeId.value : null,
      )
    }
    catch (e) {
      parseError.value = e instanceof Error ? e.message : String(e)
      document.value = null
    }
  }

  function applySimulation() {
    reloadWithPreview()
  }

  function reloadWithPreview() {
    if (!document.value?.rawYaml) {
      return
    }
    loadYaml(document.value.rawYaml, document.value.source)
  }

  function setSimulationInput(key: string, value: unknown) {
    previewInputs.value = { ...previewInputs.value, [key]: value }
    const meta = document.value?.nodes.find(n => n.kind === 'blueprint_meta')
    if (meta) {
      const sim = {
        ...(meta.data.simulationValues as Record<string, unknown> | undefined),
        [key]: value,
      }
      meta.data.simulationValues = sim
    }
  }

  function persistSimulationCatalog(catalog: SimulationCatalog) {
    simulationCatalog.value = catalog
    saveSimulationCatalog(catalog)
  }

  function highlightInputBindings(inputKey: string) {
    if (!document.value) {
      return
    }
    const { nodeIds, edgeIds } = getBindingHighlight(
      'blueprint_meta',
      inputKey,
      document.value.nodes,
      document.value.edges,
    )
    applyPathHighlight(nodeIds, edgeIds)
    pathFilterNodeId.value = null
  }

  function highlightVariableBindings(variableNodeId: string) {
    if (!document.value) {
      return
    }
    const { nodeIds, edgeIds } = getBindingHighlight(
      variableNodeId,
      undefined,
      document.value.nodes,
      document.value.edges,
    )
    applyPathHighlight(nodeIds, edgeIds)
    pathFilterNodeId.value = null
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
    updateSimulationActiveForTrigger(
      document.value.nodes.find(n => n.id === id)?.kind === 'trigger' ? id : null,
    )
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
    updateSimulationActiveForTrigger(
      document.value.nodes.find(n => n.id === id)?.kind === 'trigger' ? id : null,
    )
  }

  function clearPathFocus() {
    pathFilterNodeId.value = null
    clearPathHighlight()
    simulationActiveNodeIds.value = new Set()
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
    simulationCatalog,
    parseError,
    appMode,
    traceOverlay,
    highlightedNodeIds,
    pathHighlightNodeIds,
    pathHighlightEdgeIds,
    pathFilterNodeId,
    pathFilterNode,
    pathFilterNodeIds,
    simulationActiveNodeIds,
    rawYamlPanel,
    isDirty,
    loadYaml,
    reloadWithPreview,
    applySimulation,
    setSimulationInput,
    saveSimulationCatalog: persistSimulationCatalog,
    highlightInputBindings,
    highlightVariableBindings,
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
