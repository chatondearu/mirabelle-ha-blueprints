import type { FlowDocument, FlowNode } from '@mirabelle/flow-shared'
import { stringifyYaml } from './yaml.js'

export interface MutableFlowDocument extends FlowDocument {
  _dirty?: boolean
}

export function serializeDocument(doc: MutableFlowDocument): string {
  if (doc.rawYaml && !doc._dirty) {
    return doc.rawYaml
  }

  const root = buildConfigFromDocument(doc)
  if (doc.kind === 'blueprint' && doc.fullRoot?.blueprint) {
    return stringifyYaml({
      blueprint: doc.fullRoot.blueprint,
      ...root,
    })
  }
  return stringifyYaml(root)
}

export function buildConfigFromDocument(doc: FlowDocument): Record<string, unknown> {
  const base = { ...(doc.configRoot ?? {}) }

  const actionNodes = doc.nodes
    .filter(n => n.kind === 'action' && (n.path.startsWith('action/') || n.path.startsWith('sequence/')))
    .sort((a, b) => comparePaths(a.path, b.path))

  if (actionNodes.length > 0) {
    const actions = actionNodes.map(n => ({ ...n.data }))
    if (doc.kind === 'script' || 'sequence' in base) {
      base.sequence = actions
      delete base.action
      delete base.actions
    }
    else {
      base.action = actions.length === 1 ? actions[0] : actions
      delete base.actions
    }
  }

  applyNodeUpdates(doc, base)
  return base
}

function comparePaths(a: string, b: string): number {
  const pa = a.split('/').map(p => (Number.isNaN(Number(p)) ? p : Number(p)))
  const pb = b.split('/').map(p => (Number.isNaN(Number(p)) ? p : Number(p)))
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const va = pa[i]
    const vb = pb[i]
    if (va === undefined) {
      return -1
    }
    if (vb === undefined) {
      return 1
    }
    if (va < vb) {
      return -1
    }
    if (va > vb) {
      return 1
    }
  }
  return 0
}

function applyNodeUpdates(doc: FlowDocument, base: Record<string, unknown>): void {
  for (const node of doc.nodes) {
    if (node.kind === 'variables' && node.path === 'variables') {
      base.variables = { ...node.data }
    }
    if (node.kind === 'variable' && node.path.startsWith('variables/')) {
      const name = node.path.replace(/^variables\//, '')
      const vars =
        base.variables && typeof base.variables === 'object'
          ? { ...(base.variables as Record<string, unknown>) }
          : {}
      vars[name] = node.data.value ?? node.data
      base.variables = vars
    }
    if (node.kind === 'trigger') {
      const idx = Number(node.path.split('/')[1])
      const triggers = normalizeList(base.triggers ?? base.trigger)
      if (!Number.isNaN(idx) && triggers[idx]) {
        triggers[idx] = { ...node.data }
        if (base.triggers) {
          base.triggers = triggers
        }
        else {
          base.trigger = triggers
        }
      }
    }
  }
}

function normalizeList(value: unknown): unknown[] {
  if (Array.isArray(value)) {
    return value
  }
  if (value !== undefined) {
    return [value]
  }
  return []
}

export function updateNodeData(
  doc: MutableFlowDocument,
  nodeId: string,
  data: Record<string, unknown>,
): void {
  const node = doc.nodes.find(n => n.id === nodeId)
  if (!node) {
    return
  }
  node.data = { ...data }
  node.label = labelForNode(node)
  doc._dirty = true
}

function labelForNode(node: FlowNode): string {
  if (node.kind === 'action' && typeof node.data.service === 'string') {
    return node.data.service
  }
  return node.label
}
