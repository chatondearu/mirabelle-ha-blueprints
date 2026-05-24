# Mirabelle Flow

Mirabelle Flow is a visual editor for Home Assistant automations and Mirabelle blueprint YAML. It helps you understand branching (`choose`, conditions) as a graph and aligns node paths with Home Assistant trace paths for debugging.

## Requirements

- Node.js 20+ and pnpm 10+
- Home Assistant **2025.5.3+** (for the HA panel integration)

## Local development (Phase 1)

From the monorepo root:

```bash
pnpm install
pnpm run dev:flow
```

Open the Vite dev server URL (default `http://localhost:5173`).

### Features (local mode)

- **Repo blueprints** — load any file under `blueprints/` from the sidebar
- **Local files** — open YAML via file picker or paste
- **Graph view** — triggers, conditions, actions, `choose` branches
- **Blueprint simulation** — edit all inputs on the meta node; HA-first entity picker + local catalog
- **Binding edges** — dashed links from inputs and variables to the nodes that use them
- **Variable nodes** — one node per `variables:` key with usage links
- **Export YAML** — download (unchanged file when not edited)
- **Trace import** — paste exported trace JSON to highlight executed paths

### Simulation workflow

1. Load a blueprint from the repo sidebar.
2. Select the **blueprint_meta** node (first node) or use the inspector.
3. Toggle **Simulation mode** and edit input values (entity dropdown uses HA entities when connected, else the **Simulation catalog** in the sidebar).
4. Click **Apply simulation** — the graph reloads with substituted values and richer action labels.
5. Click **Show usages on graph** on an input to highlight `input_binding` edges.
6. Select a **variable** node to see consumers and highlight `variable_binding` edges.
7. With simulation on, select a **trigger** to see branches that statically reference that trigger (green ring).

### Limitations

- Jinja templates are not fully evaluated (static reference detection only).
- Large blueprints may parse partially.
- Simulation values are not written back to the YAML file (UI layer only).

## Home Assistant panel (Phase 2)

1. Build the frontend bundle:

   ```bash
   pnpm run build:flow:ha
   ```

2. Copy or symlink `packages/mirabelle-flow/custom_components/mirabelle_flow` into `<config>/custom_components/`.

3. Restart Home Assistant.

4. **Settings → Devices & services → Add integration → Mirabelle Flow**

5. Open **Mirabelle Flow** in the sidebar (admin only).

### HA mode

- List and open automations/scripts from your instance
- Save automation YAML back via the config API
- Node layout stored in `.storage` (does not modify automation logic)
- Load traces via WebSocket `trace/list` and `trace/get`

### Dev against a live HA instance

Set in `packages/mirabelle-flow/flow-ui/.env.local`:

```env
VITE_HA_URL=http://homeassistant.local:8123
```

Use a long-lived access token via the browser console for standalone dev: `window.hassToken = '...'`.

## Testing

```bash
pnpm run test:flow
pnpm run build:flow
```

CI runs `build:flow` and flow-core Vitest on every push to `main`.

## Architecture

| Package | Role |
|---------|------|
| `@mirabelle/flow-shared` | Types, Zod schemas, blueprint fixtures |
| `@mirabelle/flow-core` | YAML ↔ graph IR |
| `@mirabelle/flow-ui` | Vue 3 + Vite + Reka UI + UnoCSS + Vue Flow |

Inspired by [C.A.F.E.](https://github.com/FezVrasta/cafe-hass) (native YAML, optional visual layout metadata).

## Roadmap

- Full blueprint `!input` round-trip in exported YAML
- Jinja evaluation for derived variables
- Breakpoints via HA `trace/debug/*` WebSocket API
