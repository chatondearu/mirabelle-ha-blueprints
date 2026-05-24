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
- **Blueprint preview** — substitute `!input` with mock values in the inspector
- **Export YAML** — download (unchanged file when not edited)
- **Trace import** — paste exported trace JSON to highlight executed paths

### Limitations (M0)

- Complex templates (Jinja) are shown as raw node JSON, not structured editors
- Large blueprints (e.g. `cover_solar_thermal_optimization`) may parse partially
- Blueprint round-trip with `!input` tags is preview-only until a later milestone

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

- Full blueprint `!input` round-trip
- Local simulation with mock entity states
- Breakpoints via HA `trace/debug/*` WebSocket API
