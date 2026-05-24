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
