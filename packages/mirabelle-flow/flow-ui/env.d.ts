/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_HA_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  interface Window {
    hassUrl?: string
    hassToken?: string
  }
}

export {}
