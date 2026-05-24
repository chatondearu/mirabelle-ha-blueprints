# Mirabelle Flow

Visual workflow editor for Home Assistant automations and Mirabelle blueprints.

## Development

From the monorepo root:

```bash
pnpm install
pnpm run dev:flow
```

Build for Home Assistant panel:

```bash
pnpm run build:flow:ha
```

Copy `custom_components/mirabelle_flow` into your HA `config/custom_components/` directory (or install via HACS when synced).

## Packages

- `@mirabelle/flow-shared` — types and Zod schemas
- `@mirabelle/flow-core` — YAML parse/serialize and graph builder
- `@mirabelle/flow-ui` — Vue 3 + Vite frontend

See [docs/mirabelle-flow.md](../../docs/mirabelle-flow.md) for full documentation.
