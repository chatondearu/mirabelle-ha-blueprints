import { resolve } from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@mirabelle/flow-shared': resolve(__dirname, '../flow-shared/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
})
