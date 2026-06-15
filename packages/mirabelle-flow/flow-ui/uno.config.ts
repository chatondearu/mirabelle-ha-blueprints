import { defineConfig, presetIcons, presetUno } from 'unocss'
import { FLOW_NODE_UI_SAFELIST } from './src/styles/flow-node-ui'
import { NODE_ICON_SAFELIST } from './src/styles/flow-node-theme'

export default defineConfig({
  content: {
    filesystem: [
      'src/**/*.{vue,ts}',
    ],
  },
  safelist: [
    ...NODE_ICON_SAFELIST,
    ...FLOW_NODE_UI_SAFELIST,
  ],
  shortcuts: {
    'flow-node-title': 'min-w-0 truncate whitespace-nowrap',
    'flow-node-label': 'truncate whitespace-nowrap',
    'flow-node-icon': 'inline-block size-4 shrink-0 opacity-90 text-neutral-300',
    'flow-canvas': 'mirabelle-flow-canvas h-full w-full bg-neutral-950',
    'flow-canvas-empty': 'flex h-full items-center justify-center text-neutral-500',
  },
  preflights: [
    {
      getCSS: () => `
.mirabelle-flow-canvas .vue-flow__node,
.mirabelle-flow-canvas .vue-flow__node-default,
.mirabelle-flow-canvas .vue-flow__node.selectable,
.mirabelle-flow-canvas .vue-flow__node.selected {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  box-shadow: none !important;
}
.mirabelle-flow-canvas .vue-flow__node-parent {
  overflow: visible;
}
`,
    },
  ],
  presets: [
    presetUno(),
    presetIcons({
      scale: 1.1,
      collections: {
        lucide: () => import('@iconify-json/lucide/icons.json').then(i => i.default),
      },
    }),
  ],
})
