import type { FlowNodeKind } from '@mirabelle/flow-shared'

export interface HaBlockDescriptor {
  key: string
  nodeKind: FlowNodeKind
  summary: (block: Record<string, unknown>) => string
}

const DEFAULT_DESCRIPTOR: HaBlockDescriptor = {
  key: 'action',
  nodeKind: 'action',
  summary: () => 'Action',
}

export const HA_BLOCK_REGISTRY: HaBlockDescriptor[] = [
  {
    key: 'service',
    nodeKind: 'action',
    summary: block => String(block.service ?? 'Action'),
  },
  {
    key: 'choose',
    nodeKind: 'choose',
    summary: () => 'Choose',
  },
  {
    key: 'delay',
    nodeKind: 'delay',
    summary: block => `Delay: ${JSON.stringify(block.delay)}`,
  },
  {
    key: 'wait_template',
    nodeKind: 'wait',
    summary: () => 'Wait template',
  },
  {
    key: 'wait_for_trigger',
    nodeKind: 'wait',
    summary: () => 'Wait for trigger',
  },
  {
    key: 'repeat',
    nodeKind: 'repeat',
    summary: () => 'Repeat',
  },
  {
    key: 'parallel',
    nodeKind: 'parallel',
    summary: () => 'Parallel',
  },
  {
    key: 'sequence',
    nodeKind: 'sequence',
    summary: () => 'Sequence',
  },
  {
    key: 'if',
    nodeKind: 'ha_block',
    summary: () => 'If',
  },
  {
    key: 'stop',
    nodeKind: 'ha_block',
    summary: block => `Stop: ${String(block.stop ?? 'all')}`,
  },
  {
    key: 'variables',
    nodeKind: 'ha_block',
    summary: () => 'Set variables',
  },
  {
    key: 'event',
    nodeKind: 'ha_block',
    summary: block => `Event: ${String(block.event ?? '')}`,
  },
  {
    key: 'scene',
    nodeKind: 'ha_block',
    summary: block => `Scene: ${String(block.scene ?? '')}`,
  },
  {
    key: 'device_action',
    nodeKind: 'ha_block',
    summary: block => `Device: ${String(block.device ?? block.entity_id ?? '')}`,
  },
]

export function getHaBlockDescriptor(block: Record<string, unknown>): HaBlockDescriptor {
  for (const descriptor of HA_BLOCK_REGISTRY) {
    if (descriptor.key in block) {
      return descriptor
    }
  }
  return DEFAULT_DESCRIPTOR
}

