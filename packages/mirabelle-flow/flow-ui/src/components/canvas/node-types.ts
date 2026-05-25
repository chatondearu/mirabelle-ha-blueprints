import type { FlowNodeKind } from '@mirabelle/flow-shared'
import type { NodeProps } from '@vue-flow/core'
import type { NodeHandleVisibility } from './composables/node-handle-visibility'

export interface FlowCanvasNodeData {
  nodeId: string
  label: string
  kind: FlowNodeKind
  rawData?: Record<string, unknown>
  highlightedItems?: string[]
  highlighted?: boolean
  pathActive?: boolean
  pathDimmed?: boolean
  pathFocus?: boolean
  simulationActive?: boolean
  handles: NodeHandleVisibility
}

export type FlowCanvasNodeProps = NodeProps<FlowCanvasNodeData>

