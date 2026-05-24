import type { FlowDocument, TraceOverlay, TraceStep } from '@mirabelle/flow-shared'

/** Map HA trace paths to flow node ids. */
export function pathToNodeId(tracePath: string): string {
  return tracePath.replace(/\//g, '_')
}

export function buildTraceOverlay(
  runId: string,
  traceData: Record<string, unknown>,
): TraceOverlay {
  const steps: TraceStep[] = []
  const activePaths = new Set<string>()

  function walk(obj: unknown, prefix: string): void {
    if (!obj || typeof obj !== 'object') {
      return
    }
    const record = obj as Record<string, unknown>
    if (record.path && typeof record.path === 'string') {
      const path = record.path as string
      activePaths.add(path)
      steps.push({
        path,
        timestamp: typeof record.timestamp === 'string' ? record.timestamp : undefined,
        result: typeof record.result === 'string' ? record.result : undefined,
        error: typeof record.error === 'string' ? record.error : undefined,
        changed_variables:
          typeof record.changed_variables === 'object'
            ? (record.changed_variables as Record<string, unknown>)
            : undefined,
      })
    }
    for (const [key, value] of Object.entries(record)) {
      if (key === 'path' || key === 'changed_variables') {
        continue
      }
      const childPath = prefix ? `${prefix}/${key}` : key
      if (Array.isArray(value)) {
        value.forEach((item, i) => walk(item, `${childPath}/${i}`))
      }
      else if (value && typeof value === 'object') {
        walk(value, childPath)
      }
    }
  }

  const trace = traceData.trace ?? traceData
  walk(trace, '')

  steps.sort((a, b) => {
    const da = a.timestamp ?? ''
    const db = b.timestamp ?? ''
    return da.localeCompare(db)
  })

  return { runId, steps, activePaths }
}

export function applyTraceToDocument(
  doc: FlowDocument,
  overlay: TraceOverlay,
): Set<string> {
  const highlighted = new Set<string>()
  for (const path of overlay.activePaths) {
    const nodeId = pathToNodeId(path)
    if (doc.nodes.some(n => n.id === nodeId || n.path === path)) {
      highlighted.add(nodeId)
    }
    for (const node of doc.nodes) {
      if (node.path === path || node.path.startsWith(`${path}/`)) {
        highlighted.add(node.id)
      }
    }
  }
  return highlighted
}

/** Parse exported trace JSON (local dev mode). */
export function parseTraceJson(json: unknown): TraceOverlay {
  if (!json || typeof json !== 'object') {
    throw new Error('Invalid trace JSON')
  }
  const o = json as Record<string, unknown>
  const runId = typeof o.run_id === 'string' ? o.run_id : 'local'
  return buildTraceOverlay(runId, o)
}
