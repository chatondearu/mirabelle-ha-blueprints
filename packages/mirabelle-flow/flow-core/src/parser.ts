import type {
  BlueprintInputDef,
  DocumentKind,
  FlowDocument,
  FlowListItem,
  FlowViewMode,
} from '@mirabelle/flow-shared'
import {
  BLUEPRINT_INPUT_FIXTURES,
  buildSimulationValues,
  type SimulationCatalog,
} from '@mirabelle/flow-shared'
import { analyzeBindings } from './binding-analyzer.js'
import { enrichNodeLabels } from './enrich-labels.js'
import {
  autoLayout,
  buildGraphFromConfig,
} from './graph-builder.js'
import {
  detectDocumentKind,
  extractBlueprintMeta,
  parseYaml,
  substituteInputs,
} from './yaml.js'

export interface ParseOptions {
  source?: string
  previewInputs?: Record<string, unknown>
  preview?: boolean
  simulationCatalog?: SimulationCatalog
  viewMode?: FlowViewMode
}

/** Unwrap nested `script:` / `automation:` blocks sometimes used in blueprint YAML. */
function normalizeConfigRoot(config: Record<string, unknown>): Record<string, unknown> {
  for (const key of ['script', 'automation'] as const) {
    const block = config[key]
    if (block && typeof block === 'object' && !Array.isArray(block)) {
      const { [key]: _removed, ...rest } = config
      return { ...rest, ...(block as Record<string, unknown>) }
    }
  }
  return config
}

export function resolveSimulationValues(
  inputs: BlueprintInputDef[],
  options: ParseOptions,
): Record<string, unknown> {
  const fileName = options.source?.split('/').pop() ?? ''
  const fixture = BLUEPRINT_INPUT_FIXTURES[fileName] ?? {}
  const catalog = options.simulationCatalog
  if (catalog) {
    return buildSimulationValues(inputs, catalog, {
      ...fixture,
      ...options.previewInputs,
    })
  }
  const values: Record<string, unknown> = {}
  for (const input of inputs) {
    values[input.key] =
      options.previewInputs?.[input.key]
      ?? fixture[input.key]
      ?? input.default
      ?? ''
  }
  return values
}

export function parseAutomationYaml(
  yamlText: string,
  options: ParseOptions = {},
): FlowDocument {
  const parsed = parseYaml(yamlText)
  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Invalid YAML: expected mapping at root')
  }

  let root = parsed as Record<string, unknown>
  let kind: DocumentKind = 'automation'
  let blueprintMeta: FlowDocument['blueprintMeta']
  let configRoot: Record<string, unknown> = root
  let alias: string | undefined
  let mode: string | undefined
  let simulationValues: Record<string, unknown> = {}
  let inputItems: FlowListItem[] = []
  const viewMode = options.viewMode ?? 'split'

  const detected = detectDocumentKind(root)

  if (detected.kind === 'blueprint') {
    kind = 'blueprint'
    const bp = root.blueprint as Record<string, unknown>
    blueprintMeta = extractBlueprintMeta(bp)
    const { blueprint, ...rest } = root
    configRoot = normalizeConfigRoot(rest)
    mode = typeof configRoot.mode === 'string' ? configRoot.mode : undefined
    simulationValues = resolveSimulationValues(blueprintMeta.inputs, options)
    inputItems = blueprintMeta.inputs.map(input => ({
      key: input.key,
      label: input.name ?? input.key,
      value: simulationValues[input.key],
      valueType: typeof simulationValues[input.key],
      group: 'input',
      meta: { selector: input.selector, description: input.description },
    }))
  }
  else if (detected.kind === 'instance') {
    kind = 'instance'
    alias = typeof root.alias === 'string' ? root.alias : undefined
    mode = typeof root.mode === 'string' ? root.mode : undefined
    configRoot = root
  }
  else if (detected.kind === 'script') {
    kind = 'script'
    mode = typeof root.mode === 'string' ? root.mode : undefined
    configRoot = root
  }
  else {
    alias = typeof root.alias === 'string' ? root.alias : undefined
    mode = typeof root.mode === 'string' ? root.mode : undefined
    configRoot = root
  }

  let workingConfig = { ...configRoot }

  if (options.preview && blueprintMeta) {
    workingConfig = substituteInputs(workingConfig, simulationValues) as Record<
      string,
      unknown
    >
  }

  const { nodes, edges } = buildGraphFromConfig(workingConfig, {
    alias: alias ?? blueprintMeta?.name ?? 'Flow',
    mode,
    viewMode,
    inputItems,
  })

  if (blueprintMeta) {
    const metaNode = {
      id: 'blueprint_meta',
      kind: 'blueprint_meta' as const,
      label: blueprintMeta.name ?? 'Blueprint',
      path: 'blueprint',
      data: {
        meta: blueprintMeta,
        inputs: blueprintMeta.inputs,
        simulationValues,
      },
      layer: 'blueprint' as const,
    }
    nodes.unshift(metaNode)
    const rootNode = nodes.find(n => n.kind === 'root')
    if (rootNode) {
      edges.unshift({
        id: 'e-blueprint',
        source: metaNode.id,
        target: rootNode.id,
        label: 'automation',
        edgeKind: 'flow' as const,
      })
    }
  }

  const bindingEdges = analyzeBindings(nodes)
  edges.push(...bindingEdges)

  if (options.preview) {
    enrichNodeLabels({ nodes, edges } as FlowDocument)
  }

  const layout = autoLayout(nodes, edges)

  return {
    kind,
    source: options.source,
    alias,
    mode,
    blueprintMeta,
    nodes,
    edges,
    layout,
    rawYaml: yamlText,
    configRoot,
    fullRoot: root,
  }
}
