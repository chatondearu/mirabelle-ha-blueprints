import type { FlowNodeKind } from '@mirabelle/flow-shared'

/**
 * Semantic role of a Home Assistant YAML mapping, inferred from its fields
 * (not from the parent list key like `action` / `conditions` / `sequence`).
 */
export type HaItemRole =
  | 'condition'
  | 'trigger'
  | 'choose'
  | 'if'
  | 'repeat'
  | 'parallel'
  | 'sequence'
  | 'service'
  | 'delay'
  | 'wait'
  | 'block'

export function isHaConditionItem(item: Record<string, unknown>): boolean {
  return typeof item.condition === 'string'
}

export function isHaTriggerItem(item: Record<string, unknown>): boolean {
  if (isHaConditionItem(item)) {
    return false
  }
  if (typeof item.platform === 'string') {
    return true
  }
  if (typeof item.trigger === 'string') {
    return true
  }
  return false
}

/** Classify a YAML object by its own keys (HA shape), independent of list context. */
export function classifyHaItem(item: Record<string, unknown>): HaItemRole {
  if (isHaConditionItem(item)) {
    return 'condition'
  }
  if (isHaTriggerItem(item)) {
    return 'trigger'
  }
  if ('choose' in item) {
    return 'choose'
  }
  if ('if' in item) {
    return 'if'
  }
  if ('repeat' in item) {
    return 'repeat'
  }
  if ('parallel' in item) {
    return 'parallel'
  }
  if (Array.isArray(item.sequence)) {
    return 'sequence'
  }
  if (typeof item.service === 'string') {
    return 'service'
  }
  if (item.delay !== undefined) {
    return 'delay'
  }
  if (
    item.wait_template !== undefined
    || item.wait_for_trigger !== undefined
    || 'wait' in item
  ) {
    return 'wait'
  }
  return 'block'
}

export function nodeKindForHaItemRole(role: HaItemRole): FlowNodeKind {
  switch (role) {
    case 'condition':
      return 'condition'
    case 'trigger':
      return 'trigger'
    case 'choose':
      return 'choose'
    case 'if':
      return 'if'
    case 'repeat':
      return 'repeat'
    case 'parallel':
      return 'parallel'
    case 'sequence':
      return 'sequence'
    case 'service':
      return 'action'
    case 'delay':
      return 'delay'
    case 'wait':
      return 'wait'
    case 'block':
      return 'ha_block'
  }
}
