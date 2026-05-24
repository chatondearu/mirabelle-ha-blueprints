import { useFlowStore } from '@/stores/flow'

export function useYamlIO() {
  const store = useFlowStore()

  async function openFile(): Promise<void> {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.yaml,.yml'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) {
        return
      }
      const text = await file.text()
      store.loadYaml(text, file.name)
    }
    input.click()
  }

  function loadText(yaml: string, source?: string) {
    store.loadYaml(yaml, source)
  }

  function downloadYaml() {
    const yaml = store.exportYaml()
    const blob = new Blob([yaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = store.document?.source ?? 'automation.yaml'
    a.click()
    URL.revokeObjectURL(url)
  }

  return { openFile, loadText, downloadYaml }
}
