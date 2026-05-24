/** Node kinds aligned with Home Assistant automation structure. */
export type FlowNodeKind =
  | 'trigger'
  | 'condition'
  | 'action'
  | 'choose'
  | 'sequence'
  | 'parallel'
  | 'repeat'
  | 'delay'
  | 'wait'
  | 'variables'
  | 'blueprint_input'
  | 'blueprint_meta'
  | 'root'

export type DocumentKind = 'automation' | 'script' | 'blueprint' | 'instance'

export interface FlowPosition {
  x: number
  y: number
}

export interface FlowNode {
  id: string
  kind: FlowNodeKind
  label: string
  path: string
  data: Record<string, unknown>
  parentId?: string
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  label?: string
  branch?: 'default' | 'true' | 'false' | string
}

export interface BlueprintInputDef {
  key: string
  name?: string
  description?: string
  default?: unknown
  selector?: Record<string, unknown>
}

export interface BlueprintMeta {
  name?: string
  description?: string
  domain?: string
  minVersion?: string
  inputs: BlueprintInputDef[]
}

export interface FlowDocument {
  kind: DocumentKind
  source?: string
  alias?: string
  mode?: string
  blueprintMeta?: BlueprintMeta
  nodes: FlowNode[]
  edges: FlowEdge[]
  layout: Record<string, FlowPosition>
  rawYaml?: string
  /** Parsed YAML root (without blueprint wrapper) for round-trip. */
  configRoot?: Record<string, unknown>
  /** Full document including blueprint block when applicable. */
  fullRoot?: Record<string, unknown>
}

export interface TraceStep {
  path: string
  timestamp?: string
  result?: string
  error?: string
  changed_variables?: Record<string, unknown>
}

export interface TraceOverlay {
  runId: string
  steps: TraceStep[]
  activePaths: Set<string>
}
