/** Visual / logical grouping for canvas layout and styling. */
export type FlowNodeLayer = 'blueprint' | 'automation'

/** Edge semantics: execution path vs semantic cross-links. */
export type FlowEdgeKind =
  | 'flow'
  | 'reference'
  | 'input_binding'
  | 'variable_binding'

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
  | 'variable'
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
  /** Defaults from kind via `getNodeLayer()` when omitted. */
  layer?: FlowNodeLayer
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  label?: string
  branch?: 'default' | 'true' | 'false' | string
  /** `flow` = solid execution path; `reference` = dashed link (e.g. trigger → condition). */
  edgeKind?: FlowEdgeKind
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

/** Reusable entity ids for simulation (persisted in localStorage). */
export interface SimulationCatalog {
  lights: string[]
  sensors: string[]
  switches: string[]
  media_players: string[]
  alarm_control_panels: string[]
  /** Generic defaults keyed by domain or custom label */
  defaults: Record<string, string>
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
