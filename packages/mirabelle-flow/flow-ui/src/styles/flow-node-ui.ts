import type { FlowNodeKind } from '@mirabelle/flow-shared'

export type FlowNodeUiRole = 'leaf' | 'child' | 'group'

export type FlowNodeUiVariation = 'palette' | 'role' | 'depth' | 'neon'
  | 'pathDimmed' | 'pathFocus' | 'simulationActive' | 'highlighted'

/** Semantic palette keys (kind + special ha_block conditions group). */
export type FlowNodePalette = FlowNodeKind | 'conditions'

/** Important modifiers: palette must win over any neutral fallback in the cascade. */
export const FLOW_NODE_PALETTE_CLASS: Record<FlowNodePalette, string> = {
  trigger: '!border-amber-500 !bg-amber-950',
  condition: '!border-blue-500 !bg-blue-950',
  action: '!border-emerald-500 !bg-emerald-950',
  choose: '!border-purple-500 !bg-purple-950',
  if: '!border-slate-500 !bg-slate-800',
  sequence: '!border-indigo-500 !bg-indigo-950',
  parallel: '!border-violet-500 !bg-violet-950',
  repeat: '!border-fuchsia-500 !bg-fuchsia-950',
  delay: '!border-orange-500 !bg-orange-950',
  wait: '!border-orange-400 !bg-orange-950/80',
  variables: '!border-cyan-500 !bg-cyan-950',
  blueprint: '!border-pink-500 !bg-pink-950',
  choose_option: '!border-purple-400 !bg-purple-950/80',
  variable: '!border-teal-500 !bg-teal-950',
  blueprint_input: '!border-pink-400/80 !bg-pink-950/60',
  ha_block: '!border-neutral-500 !bg-neutral-900',
  conditions: '!border-blue-500 !bg-blue-950',
}

export const FLOW_NODE_NEON_CLASS = {
  emerald: 'shadow-[0_0_10px_rgba(52,211,153,0.85),0_0_22px_rgba(52,211,153,0.4)]',
  amber: 'shadow-[0_0_10px_rgba(251,191,36,0.9),0_0_22px_rgba(251,191,36,0.45)]',
  blue: 'shadow-[0_0_10px_rgba(96,165,250,0.9),0_0_22px_rgba(96,165,250,0.45)]',
  pink: 'shadow-[0_0_10px_rgba(244,114,182,0.9),0_0_22px_rgba(244,114,182,0.45)]',
  teal: 'shadow-[0_0_10px_rgba(45,212,191,0.9),0_0_22px_rgba(45,212,191,0.45)]',
} as const

export type FlowNodeNeonTone = keyof typeof FLOW_NODE_NEON_CLASS

export const FLOW_NODE_UI_CONFIG = {
  default: {},
  card: {
    base: [
      'box-border rounded-lg border-2 border-solid p-2 text-sm leading-tight',
      'shadow-lg transition-all duration-200 ease-in-out',
    ],
    variations: {
      palette: FLOW_NODE_PALETTE_CLASS,
      role: {
        leaf: 'w-64 max-w-64 h-14 flex flex-col justify-center',
        child: 'min-w-32 max-w-56 px-2 py-1.5 text-xs cursor-default',
        group: 'w-full max-w-none min-h-16 h-full',
      },
      depth: {
        1: '!border-0 shadow-none',
        2: '!border-0 shadow-none',
        3: '!border-0 shadow-none',
      },
      neon: FLOW_NODE_NEON_CLASS,
      pathDimmed: 'opacity-20 saturate-50',
      pathFocus: 'outline outline-2 outline-white/50 outline-offset-2',
      simulationActive: 'outline outline-2 outline-emerald-300/80 outline-offset-2',
      highlighted: 'outline outline-2 outline-yellow-400 outline-offset-2',
    },
  },
  title: {
    base: 'flow-node-title min-w-0 font-medium',
  },
  label: {
    base: 'flow-node-label text-neutral-300',
  },
  icon: {
    base: 'flow-node-icon',
  },
}

/** Split utility strings so UnoCSS safelist emits each class (space-separated entries are ignored). */
export function splitUnoTokens(...sources: string[]): string[] {
  return [...new Set(sources.flatMap(s => s.trim().split(/\s+/).filter(Boolean)))]
}

const CARD_ROLE_CLASS = Object.values(FLOW_NODE_UI_CONFIG.card.variations.role)
const CARD_DEPTH_CLASS = Object.values(FLOW_NODE_UI_CONFIG.card.variations.depth)
const CARD_STATE_CLASS = [
  FLOW_NODE_UI_CONFIG.card.variations.pathDimmed,
  FLOW_NODE_UI_CONFIG.card.variations.pathFocus,
  FLOW_NODE_UI_CONFIG.card.variations.simulationActive,
  FLOW_NODE_UI_CONFIG.card.variations.highlighted,
] as string[]

export const FLOW_NODE_UI_SAFELIST = splitUnoTokens(
  ...(FLOW_NODE_UI_CONFIG.card.base as string[]),
  ...Object.values(FLOW_NODE_PALETTE_CLASS),
  ...Object.values(FLOW_NODE_NEON_CLASS),
  ...CARD_ROLE_CLASS,
  ...CARD_DEPTH_CLASS,
  ...CARD_STATE_CLASS,
  FLOW_NODE_UI_CONFIG.title.base,
  FLOW_NODE_UI_CONFIG.label.base,
  FLOW_NODE_UI_CONFIG.icon.base,
)
