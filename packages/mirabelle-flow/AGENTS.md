# Agent instructions — Mirabelle Flow

Canonical guide for AI coding agents working on **Mirabelle Flow** (`packages/mirabelle-flow/`). For monorepo-wide rules (blueprints, HACS sync, conventional commits), see the root [`AGENTS.md`](../../AGENTS.md).

**User-facing docs:** [`docs/mirabelle-flow.md`](../../docs/mirabelle-flow.md) (setup, HA panel, testing).  
**UI and visual rules:** [`DESIGN.md`](./DESIGN.md).

---

## Purpose

Mirabelle Flow is a **visual editor and debugger** for Home Assistant automations and Mirabelle blueprint YAML:

1. **Phase 1 — Local dev** — Vite app to open repo blueprints, local files, or pasted YAML; graph view; blueprint preview; YAML export; trace JSON import.
2. **Phase 2 — HA panel** — `custom_components/mirabelle_flow` embeds the built UI; list/load/save automations and scripts; persist node layout in `.storage`; load traces via HA WebSocket.

Inspired by [C.A.F.E.](https://github.com/FezVrasta/cafe-hass): **YAML remains the source of truth**; layout and UI metadata must not silently rewrite automation logic.

**Target platform:** Home Assistant **2025.5.3+**.

**Language:** Chat may be in French; **all user-facing strings in code and Markdown** (labels, errors, `strings.json`, docs) must be **English**.

---

## Package layout

```
packages/mirabelle-flow/
├── AGENTS.md              ← this file
├── DESIGN.md              ← UI / design system
├── README.md              ← short overview + dev commands
├── package.json           ← workspace scripts (dev, build, test)
├── hacs.json
├── flow-shared/           ← @mirabelle/flow-shared (types, Zod, fixtures)
├── flow-core/             ← @mirabelle/flow-core (YAML ↔ graph IR, no Vue)
├── flow-ui/               ← @mirabelle/flow-ui (Vue 3 + Vite + Reka + UnoCSS)
└── custom_components/
    └── mirabelle_flow/    ← HA integration + www/ (built assets)
```

### Dependency rules

| Layer | May depend on | Must not |
|-------|----------------|----------|
| `flow-shared` | `zod` only | Vue, HA client, `yaml` parser |
| `flow-core` | `flow-shared`, `yaml`, `zod` | Vue, browser APIs, Pinia |
| `flow-ui` | `flow-core`, `flow-shared`, Vue stack | Duplicate parse/serialize logic in components |
| `custom_components` | Python stdlib + HA APIs | Business logic duplicated from TS (only panel, storage, WS API) |

**Graph IR** (`FlowDocument`, nodes, edges) lives in `flow-shared`. **Parsing and serialization** live in `flow-core`. The UI **displays and edits** the IR; it does not invent parallel YAML structures.

---

## Development commands

From the **monorepo root**:

| Command | Action |
|---------|--------|
| `pnpm run dev:flow` | Vite dev server (`flow-ui`, default `http://localhost:5173`) |
| `pnpm run test:flow` | Build `flow-shared`, then Vitest in `flow-core` |
| `pnpm run build:flow` | Build all flow packages |
| `pnpm run build:flow:ha` | Production build + copy to `custom_components/mirabelle_flow/www` |

From `packages/mirabelle-flow/flow-ui`:

- `.env.local`: `VITE_HA_URL=...` for optional live HA during standalone dev.
- Panel dev: use `window.hassToken` in the browser console when not embedded in HA.

**Before pushing flow changes:** run `pnpm run test:flow` and `pnpm run build:flow` (CI does the same via `validate.yml`).

---

## Architecture notes

### YAML and `!input`

- `flow-core` pre-processes HA `!input` tags for parsing and restores them on export where supported.
- **M0:** full blueprint `!input` round-trip is limited; preview mode substitutes fixture/mock inputs (`flow-shared` fixtures).
- Do not break `yaml.safe_load`-friendly output used elsewhere in the monorepo.

### Graph builder (M0 scope)

Supported well: triggers, conditions, service actions, `choose` branches, basic sequences.  
Partial / raw JSON in inspector: complex templates (Jinja), large nested blueprints.

When extending the parser:

1. Add or extend types in `flow-shared`.
2. Implement in `flow-core` (`graph-builder.ts`, `parser.ts`, `serializer.ts`).
3. Add **Vitest** tests with real blueprint YAML from `blueprints/` when possible.
4. Update node styling in `DESIGN.md` / `FlowNode.vue` if new `FlowNodeKind` values appear.

### Trace overlay

- HA: `trace/list`, `trace/get` via `home-assistant-js-websocket` in `useHaConnection.ts`.
- Local: user-pasted trace JSON.
- Mapping trace paths → node IDs: `flow-core/src/trace.ts`. Keep highlighting logic in the store/composable, not scattered in components.

### HA custom component

- Domain: `mirabelle_flow`.
- Panel registration: `panel.py`; static files under `www/` (generated — do not hand-edit bundles).
- Layout persistence: WebSocket `mirabelle_flow/layout/get|save` → `.storage`.
- Rebuild frontend after UI changes: `pnpm run build:flow:ha`.

---

## Frontend conventions (`flow-ui`)

Follow [`DESIGN.md`](./DESIGN.md) for visuals. Code conventions:

- **Vue 3** with `<script setup lang="ts">` only.
- **Composables** (`src/composables/`) for I/O, HA connection, and cross-view behavior.
- **Pinia** (`src/stores/flow.ts`) for document state, selection, dirty flag, trace overlay.
- **Components** under `src/components/` by area: `canvas/`, `sidebar/`, `inspector/`, `trace/`.
- **Props:** define with `defineProps` and TypeScript interfaces; avoid `any`.
- **Reka UI** for accessible primitives (tabs, labels, dialogs when added). Prefer Reka over ad-hoc ARIA.
- **UnoCSS** utility classes for layout and theme; avoid large custom CSS files unless necessary (Vue Flow overrides).
- **Comments in code:** English only.

### App modes

- `store.appMode`: `'local' | 'ha'`.
- Auto-detect HA panel via `window.location.pathname` or `window.hassUrl`.
- Sidebar: `FileExplorer` (local) vs `HaEntityList` (HA).

### Blueprint simulation

- Inputs live in flow nodes (`inputs` or `inputs_variables`) with mirrored metadata in `blueprint_meta.data`.
- **`simulationCatalog`** in Pinia + `localStorage`; entity pickers are **HA-first** via `useEntityPicker` (fallback catalog).
- **`previewMode`** defaults to on; `applySimulation()` reloads YAML through `parseAutomationYaml` with `substituteInputs`.
- **Binding edges**: `input_binding`, `variable_binding` from `binding-analyzer.ts` (not layout edges).
- **Variables list node**: `kind: 'variables'` with row-level handles (`var-<name>`) and item highlights.

### Editing and export

- `store.isDirty` drives UI indicators; export/download should reflect edited YAML when dirty.
- HA save: automation config via config API; layout via `mirabelle_flow` WebSocket — **never** mix layout into automation YAML.

---

## Testing

| Area | Tool | Location |
|------|------|----------|
| Parser / serializer / graph | Vitest | `flow-core/src/**/*.test.ts` |
| UI | Vitest (minimal for now) | `flow-ui` |
| Manual | `pnpm run dev:flow` | Load `blueprints/automations/presence_based_lighting.yaml`, etc. |

Golden tests should use **real repo blueprints** where stable. Prefer extending existing tests over one-off fixtures.

---

## Security

- No tokens, passwords, or instance URLs in committed source.
- `VITE_*` and `.env.local` are local only; document in `docs/mirabelle-flow.md`, not in code.
- HA panel is **admin-only** (enforced by HA panel registration).

---

## Commits and scope

Use conventional commits with a **scope**, e.g.:

- `feat(mirabelle-flow): add repeat-until nodes to graph builder`
- `fix(flow-ui): trace highlight for nested choose paths`
- `docs(mirabelle-flow): document HA layout API`

Do not edit public HACS mirror repos directly; this package may be synced later per monorepo sync docs.

---

## Checklist for agents

| Task | Check |
|------|--------|
| Parser / IR change | Types in `flow-shared`, logic in `flow-core`, Vitest, no Vue imports in core |
| New node kind | `FlowNodeKind`, graph builder, `FlowNode.vue` colors, `DESIGN.md` |
| UI change | `DESIGN.md`, Reka + UnoCSS, composable if shared logic |
| HA panel | `pnpm run build:flow:ha`, verify `www/` updated |
| Docs | English; update `docs/mirabelle-flow.md` if user workflow changes |
| CI | `test:flow` + `build:flow` green |
