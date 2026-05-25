import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { defineConfig } from 'vite'

const repoBlueprints = resolve(__dirname, '../../../blueprints')

export default defineConfig(({ mode }) => ({
  plugins: [vue(), UnoCSS()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      // Dev: use package sources so dist rebuild is not required after flow-shared/flow-core edits
      '@mirabelle/flow-shared': resolve(__dirname, '../flow-shared/src/index.ts'),
      '@mirabelle/flow-core': resolve(__dirname, '../flow-core/src/index.ts'),
    },
  },
  base: mode === 'ha' ? '/mirabelle-flow/' : '/',
  server: {
    fs: {
      allow: [repoBlueprints, resolve(__dirname, '../../..')],
    },
  },
  build: {
    outDir: mode === 'ha'
      ? resolve(__dirname, '../custom_components/mirabelle_flow/www')
      : 'dist',
    emptyOutDir: true,
    sourcemap: true,
  },
}))
