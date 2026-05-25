import type { FlowListItem } from '@mirabelle/flow-shared'
import type { FlowCanvasNodeData } from '../node-types'

export const LIST_BASE_TOP = 98
export const LIST_ROW_STEP = 34

export function handleTop(index: number): string {
  return `${LIST_BASE_TOP + index * LIST_ROW_STEP}px`
}

export function isHighlightedItem(data: FlowCanvasNodeData, key: string): boolean {
  return (data.highlightedItems ?? []).includes(key)
}

export function itemDisplayValue(item: FlowListItem): string {
  if (item.value === undefined || item.value === null) {
    return ''
  }
  if (Array.isArray(item.value)) {
    return item.value.join(', ')
  }
  return String(item.value)
}

