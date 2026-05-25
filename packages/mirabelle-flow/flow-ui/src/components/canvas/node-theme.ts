import type { FlowNodeKind } from '@mirabelle/flow-shared'

/** Lucide icon classes (Uno preset-icons). Colors live in node-shared.css via data-kind. */
export const NODE_KIND_ICON_CLASS: Record<FlowNodeKind, string> = {
  trigger: 'i-lucide-zap',
  condition: 'i-lucide-filter',
  action: 'i-lucide-play',
  choose: 'i-lucide-git-branch',
  sequence: 'i-lucide-list-ordered',
  parallel: 'i-lucide-layers',
  repeat: 'i-lucide-repeat',
  delay: 'i-lucide-clock',
  wait: 'i-lucide-hourglass',
  variables: 'i-lucide-braces',
  inputs: 'i-lucide-sliders-horizontal',
  inputs_variables: 'i-lucide-list-tree',
  choose_option: 'i-lucide-list',
  ha_block: 'i-lucide-box',
  blueprint_input: 'i-lucide-sliders-horizontal',
  blueprint_meta: 'i-lucide-file-code-2',
  variable: 'i-lucide-variable',
  root: 'i-lucide-workflow',
}

export const NODE_ICON_SAFELIST = [
  ...Object.values(NODE_KIND_ICON_CLASS),
  'i-lucide-circle',
]
