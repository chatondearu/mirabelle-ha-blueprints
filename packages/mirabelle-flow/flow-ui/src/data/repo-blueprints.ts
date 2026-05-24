/** Blueprint files served via Vite dev (import.meta.glob). */
export const REPO_BLUEPRINTS = import.meta.glob(
  '../../../../../blueprints/**/*.yaml',
  { query: '?raw', import: 'default', eager: false },
) as Record<string, () => Promise<string>>

export async function listRepoBlueprints(): Promise<{ path: string, name: string }[]> {
  return Object.keys(REPO_BLUEPRINTS).map((path) => {
    const name = path.split('/').pop() ?? path
    return { path, name }
  })
}

export async function loadRepoBlueprint(path: string): Promise<string> {
  const loader = REPO_BLUEPRINTS[path]
  if (!loader) {
    throw new Error(`Blueprint not found: ${path}`)
  }
  return loader()
}
