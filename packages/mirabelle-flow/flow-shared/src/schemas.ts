import { z } from 'zod'

export const flowNodeKindSchema = z.enum([
  'trigger',
  'condition',
  'action',
  'choose',
  'sequence',
  'parallel',
  'repeat',
  'delay',
  'wait',
  'variables',
  'choose_option',
  'ha_block',
  'variable',
  'blueprint_input',
  'blueprint',
])

export const flowNodeLayerSchema = z.enum(['blueprint', 'automation'])

export const flowEdgeKindSchema = z.enum([
  'flow',
  'reference',
  'input_binding',
  'variable_binding',
])

export const flowNodeSchema = z.object({
  id: z.string(),
  kind: flowNodeKindSchema,
  label: z.string(),
  path: z.string(),
  data: z.record(z.unknown()),
  parentId: z.string().optional(),
  layer: flowNodeLayerSchema.optional(),
})

export const flowEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  label: z.string().optional(),
  branch: z.string().optional(),
  edgeKind: flowEdgeKindSchema.optional(),
  sourceHandle: z.string().optional(),
  targetHandle: z.string().optional(),
  itemKey: z.string().optional(),
})

export const flowDocumentSchema = z.object({
  kind: z.enum(['automation', 'script', 'blueprint', 'instance']),
  source: z.string().optional(),
  alias: z.string().optional(),
  mode: z.string().optional(),
  nodes: z.array(flowNodeSchema),
  edges: z.array(flowEdgeSchema),
  layout: z.record(
    z.object({ x: z.number(), y: z.number() }),
  ),
})

export type FlowDocumentInput = z.infer<typeof flowDocumentSchema>
