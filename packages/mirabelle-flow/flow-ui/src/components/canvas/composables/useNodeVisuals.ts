import type { FlowCanvasNodeData } from '../node-types'
import { NODE_KIND_ICON_CLASS } from '../node-theme'
import { computed, type MaybeRefOrGetter, toValue } from 'vue'

/**
 * Node visuals for canvas components.
 * Destructure the return value in setup — nested refs are not unwrapped via `visuals.iconClass` in templates.
 */
export function useNodeVisuals(data: MaybeRefOrGetter<FlowCanvasNodeData>) {
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

  const neonClass = computed(() => {
    const d = toValue(data)
    if (!d.pathActive) {
      return ''
    }
    const kind = d.kind
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

  const stateClasses = computed(() => {
    const d = toValue(data)
    return [
      neonClass.value,
      d.pathDimmed ? 'is-path-dimmed' : '',
      d.simulationActive ? 'is-simulation-active' : '',
      d.pathFocus ? 'is-path-focus' : '',
      d.highlighted && !d.pathActive ? 'is-highlighted' : '',
    ]
  })

  return {
    iconClass,
    titleKind,
    neonClass,
    stateClasses,
  }
}
