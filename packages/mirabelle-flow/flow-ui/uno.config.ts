import { defineConfig, presetIcons, presetUno } from 'unocss'
import { NODE_ICON_SAFELIST } from './src/components/canvas/node-theme'

export default defineConfig({
  safelist: NODE_ICON_SAFELIST,
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
