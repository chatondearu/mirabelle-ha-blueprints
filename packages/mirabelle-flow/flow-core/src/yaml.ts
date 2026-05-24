import { parse, stringify } from 'yaml'

const INPUT_PATTERN = /!input\s+(\S+)/g

/** Preprocess HA !input tags into parseable scalars. */
function preprocessInputTags(text: string): string {
  return text.replace(INPUT_PATTERN, (_, key: string) => `"__input:${key}"`)
}

function postprocessInputRefs(value: unknown): unknown {
  if (typeof value === 'string' && value.startsWith('__input:')) {
    return { __input: value.slice('__input:'.length) }
  }
  if (Array.isArray(value)) {
    return value.map(postprocessInputRefs)
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) {
      out[k] = postprocessInputRefs(v)
    }
    return out
  }
  return value
}

export function parseYaml(text: string): unknown {
  const preprocessed = preprocessInputTags(text)
  const parsed = parse(preprocessed)
  return postprocessInputRefs(parsed)
}

export function stringifyYaml(value: unknown): string {
  const restored = restoreInputTags(value)
  return stringify(restored, { lineWidth: 0 })
}

function restoreInputTags(value: unknown): unknown {
  if (isInputRef(value)) {
    return `!input ${value.__input}`
  }
  if (Array.isArray(value)) {
    return value.map(restoreInputTags)
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) {
      out[k] = restoreInputTags(v)
    }
    return out
  }
  return value
}

export function isInputRef(value: unknown): value is { __input: string } {
  return (
    typeof value === 'object'
    && value !== null
    && '__input' in value
    && typeof (value as { __input: string }).__input === 'string'
  )
}

export function inputRefKey(value: unknown): string | undefined {
  if (isInputRef(value)) {
    return value.__input
  }
  return undefined
}

export function substituteInputs(
  value: unknown,
  inputs: Record<string, unknown>,
): unknown {
  if (isInputRef(value)) {
    const key = value.__input
    return key in inputs ? inputs[key] : value
  }
  if (Array.isArray(value)) {
    return value.map(v => substituteInputs(v, inputs))
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) {
      out[k] = substituteInputs(v, inputs)
    }
    return out
  }
  return value
}

export function detectDocumentKind(root: Record<string, unknown>): {
  kind: 'blueprint' | 'instance' | 'automation' | 'script'
  blueprintDomain?: string
} {
  if ('blueprint' in root && typeof root.blueprint === 'object') {
    const bp = root.blueprint as Record<string, unknown>
    const domain = typeof bp.domain === 'string' ? bp.domain : 'automation'
    return { kind: 'blueprint', blueprintDomain: domain }
  }
  if ('use_blueprint' in root) {
    return { kind: 'instance' }
  }
  if ('sequence' in root) {
    return { kind: 'script' }
  }
  return { kind: 'automation' }
}

export function extractBlueprintMeta(
  blueprintBlock: Record<string, unknown>,
): import('@mirabelle/flow-shared').BlueprintMeta {
  const inputBlock = blueprintBlock.input
  const inputs: import('@mirabelle/flow-shared').BlueprintInputDef[] = []
  if (inputBlock && typeof inputBlock === 'object') {
    for (const [key, def] of Object.entries(inputBlock as Record<string, unknown>)) {
      if (def && typeof def === 'object') {
        const d = def as Record<string, unknown>
        inputs.push({
          key,
          name: typeof d.name === 'string' ? d.name : undefined,
          description: typeof d.description === 'string' ? d.description : undefined,
          default: d.default,
          selector:
            typeof d.selector === 'object'
              ? (d.selector as Record<string, unknown>)
              : undefined,
        })
      }
    }
  }
  const ha = blueprintBlock.homeassistant as Record<string, unknown> | undefined
  return {
    name: typeof blueprintBlock.name === 'string' ? blueprintBlock.name : undefined,
    description:
      typeof blueprintBlock.description === 'string' ? blueprintBlock.description : undefined,
    domain: typeof blueprintBlock.domain === 'string' ? blueprintBlock.domain : undefined,
    minVersion:
      ha && typeof ha.min_version === 'string' ? ha.min_version : undefined,
    inputs,
  }
}
