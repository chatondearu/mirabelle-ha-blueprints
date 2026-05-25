import type { FlowCanvasNodeData } from '../node-types'
import { NODE_KIND_ICON_CLASS } from '../node-theme'
import { computed } from 'vue'

export function useNodeVisuals(data: FlowCanvasNodeData) {
  const iconClass = computed(() => NODE_KIND_ICON_CLASS[data.kind] ?? 'i-lucide-circle')

  const titleKind = computed(() => {
    if (data.kind === 'blueprint') {
      return 'Blueprint'
    }
    if (data.kind.startsWith('blueprint_')) {
      return data.kind.replace('blueprint_', '')
    }
    return data.kind
  })

  const neonClass = computed(() => {
    if (!data.pathActive) {
      return ''
    }
    const kind = data.kind
    if (kind === 'trigger') {
      return 'flow-node-neon flow-node-neon-amber'
    }
    if (kind === 'condition') {
      return 'flow-node-neon flow-node-neon-blue'
    }
    if (kind === 'variable' || kind === 'variables') {
      return 'flow-node-neon flow-node-neon-teal'
    }
    if (kind === 'blueprint' || kind === 'blueprint_input') {
      return 'flow-node-neon flow-node-neon-pink'
    }
    return 'flow-node-neon flow-node-neon-emerald'
  })

  const stateClasses = computed(() => [
    neonClass.value,
    data.pathDimmed ? 'is-path-dimmed' : '',
    data.simulationActive ? 'is-simulation-active' : '',
    data.pathFocus ? 'is-path-focus' : '',
    data.highlighted && !data.pathActive ? 'is-highlighted' : '',
  ])

  return {
    iconClass,
    titleKind,
    neonClass,
    stateClasses,
  }
}

