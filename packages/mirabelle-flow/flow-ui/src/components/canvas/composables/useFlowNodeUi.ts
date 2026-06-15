import type { FlowCanvasNodeData } from '../node-types'
import {
  type FlowNodeNeonTone,
  type FlowNodePalette,
  FLOW_NODE_UI_CONFIG,
  type FlowNodeUiRole,
  type FlowNodeUiVariation,
} from '@/styles/flow-node-ui'
import { NODE_KIND_ICON_CLASS } from '@/styles/flow-node-theme'
import { computed, type MaybeRefOrGetter, toValue } from 'vue'
import { useUnoUi, type UnoUiConfig } from 'uno-variations'

export interface UseFlowNodeUiOptions {
  role?: FlowNodeUiRole
}

function resolvePalette(data: FlowCanvasNodeData): FlowNodePalette {
  if (data.kind === 'ha_block' && data.rawData?.blockKey === 'conditions') {
    return 'conditions'
  }
  return data.kind
}

function resolveRole(
  data: FlowCanvasNodeData,
  explicit?: FlowNodeUiRole,
): FlowNodeUiRole {
  if (explicit) {
    return explicit
  }
  if (data.rawData?.isContainer === true || data.rawData?.isGroup === true) {
    return 'group'
  }
  if (data.depth > 0) {
    return 'child'
  }
  return 'leaf'
}

function resolveNeonTone(data: FlowCanvasNodeData): FlowNodeNeonTone {
  const kind = data.kind
  if (kind === 'trigger') {
    return 'amber'
  }
  if (kind === 'condition') {
    return 'blue'
  }
  if (kind === 'variable' || kind === 'variables') {
    return 'teal'
  }
  if (kind === 'blueprint' || kind === 'blueprint_input') {
    return 'pink'
  }
  return 'emerald'
}

/**
 * Flow node class resolvers (UnoCSS + uno-variations).
 * Destructure in setup — nested refs are not unwrapped via `ui.card` in templates.
 */
export function useFlowNodeUi(
  data: MaybeRefOrGetter<FlowCanvasNodeData>,
  options?: UseFlowNodeUiOptions,
) {
  const variations = computed(() => {
    const d = toValue(data)
    const depthKey = d.depth >= 1 && d.depth <= 3 ? String(d.depth) : undefined
    const isNestedChild = d.depth >= 1 && d.depth <= 3
    return {
      palette: resolvePalette(d),
      role: resolveRole(d, options?.role),
      // Nested children keep palette background; only strip border chrome.
      depth: isNestedChild ? depthKey : undefined,
      neon: d.pathActive ? resolveNeonTone(d) : undefined,
      pathDimmed: d.pathDimmed,
      pathFocus: d.pathFocus,
      simulationActive: d.simulationActive,
      highlighted: d.highlighted && !d.pathActive,
    }
  })

  const { uu } = useUnoUi(
    FLOW_NODE_UI_CONFIG as unknown as UnoUiConfig<FlowNodeUiVariation>,
    variations,
  )

  const iconClass = computed(
    () => NODE_KIND_ICON_CLASS[toValue(data).kind] ?? 'i-lucide-circle',
  )

  const titleKind = computed(() => {
    const kind = toValue(data).kind
    if (kind === 'blueprint') {
      return 'Blueprint'
    }
    if (kind.startsWith('blueprint_')) {
      return kind.replace('blueprint_', '')
    }
    return kind
  })

  function card(classes = '') {
    return uu.value.card({ classes })
  }

  function title(classes = '') {
    return uu.value.title({ classes })
  }

  function label(classes = '') {
    return uu.value.label({ classes })
  }

  function icon(classes = '') {
    return uu.value.icon({ classes })
  }

  return {
    iconClass,
    titleKind,
    card,
    title,
    label,
    icon,
  }
}
