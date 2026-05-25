import type { FlowDocument, FlowNode } from '@mirabelle/flow-shared'
import { summarizeServiceAction } from './action-expander.js'
import { isInputRef } from './yaml.js'

function truncate(text: string, max = 48): string {
  return text.length > max ? `${text.slice(0, max)}…` : text
}

function formatValue(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return ''
}

export function enrichNodeLabels(doc: FlowDocument): void {
  const simulationValues =
    (doc.nodes.find(n => n.kind === 'blueprint')?.data.simulationValues as
      | Record<string, unknown>
      | undefined)
    ?? {}
  for (const node of doc.nodes) {
    if (node.kind === 'action' && typeof node.data.service === 'string') {
      node.label = summarizeServiceAction(node.data)
    }

    if (node.kind === 'trigger') {
      const platform = (node.data.platform ?? node.data.trigger) as string | undefined
      const entity = node.data.entity_id as string | undefined
      const id = typeof node.data.id === 'string' ? node.data.id : undefined
      if (platform && entity) {
        node.label = id
          ? `Trigger: ${platform} (${entity}) [${id}]`
          : `Trigger: ${platform} (${entity})`
      }
    }

    if (node.kind === 'condition') {
      if (node.data.condition === 'trigger' && typeof node.data.id === 'string') {
        node.label = `Trigger: ${node.data.id}`
      }
      else if (
        node.data.condition === 'template'
        && typeof node.data.value_template === 'string'
      ) {
        node.label = truncate(`Template: ${node.data.value_template}`)
      }
    }

    if (node.kind === 'blueprint_input') {
      const key = node.data.key as string
      if (key && simulationValues[key] !== undefined) {
        node.data.value = simulationValues[key]
      }
    }

    if (node.kind === 'variable') {
      const raw = node.data.value
      if (isInputRef(raw)) {
        const substituted = simulationValues[raw.__input]
        if (substituted !== undefined) {
          node.label = `${node.data.name}: ← ${formatValue(substituted)}`
        }
      }
    }

    if (node.kind === 'choose' && Array.isArray(node.data.options)) {
      const options = node.data.options as Array<Record<string, unknown>>
      node.data.options = options.map((option, idx) => ({
        ...option,
        label: option.label ?? `Option ${idx + 1}`,
      }))
    }
  }
}

export function getVariablePreviewLabel(
  node: FlowNode,
  simulationValues: Record<string, unknown>,
): string {
  const name = node.path.replace(/^variables\//, '')
  const raw = node.data.value ?? node.data
  if (isInputRef(raw)) {
    const substituted = simulationValues[raw.__input]
    if (substituted !== undefined) {
      return `${name} ← ${formatValue(substituted)}`
    }
  }
  if (typeof raw === 'string' && raw.includes('split(') && isInputRef(node.data)) {
    return `${name} (computed template)`
  }
  return node.label
}
