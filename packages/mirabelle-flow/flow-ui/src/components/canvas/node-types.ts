import type { FlowNodeKind } from '@mirabelle/flow-shared'
import type { NodeProps } from '@vue-flow/core'

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
}

export type FlowCanvasNodeProps = NodeProps<FlowCanvasNodeData>

