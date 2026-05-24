# Mirabelle Flow — Design system

Visual and interaction guidelines for `@mirabelle/flow-ui`. Agents and contributors should follow this document when adding or changing UI. Implementation stack: **Vue 3**, **Reka UI**, **UnoCSS**, **@vue-flow/core**.

---

## Design principles

1. **Clarity over decoration** — The graph is the primary surface; chrome stays compact and low-contrast.
2. **Semantic color** — Node border/background colors encode Home Assistant structure (trigger vs action vs branch), not arbitrary branding.
3. **Dark-first** — Default theme is dark to match Home Assistant’s UI and reduce eye strain during long debugging sessions.
4. **Trace as truth** — Executed paths must be obvious (highlight + timeline); non-executed branches stay visually subdued.
5. **Progressive disclosure** — Sidebar and inspector show detail on demand; the canvas stays uncluttered.
6. **Native HA feel in panel mode** — When embedded in Home Assistant, avoid jarring bright surfaces; align with neutral/emerald accents already used in the header.

---

## Layout

### Shell (desktop)

```
┌─────────────────────────────────────────────────────────────┐
│ Header: title · mode toggle · doc name · actions          │
├──────────┬────────────────────────────────────┬─────────────┤
│ Sidebar  │           Flow canvas            │  Inspector  │
│  w-56    │         (Vue Flow, flex-1)       │    w-72     │
│          ├────────────────────────────────────┤             │
│          │     Trace timeline (h-36)        │             │
└──────────┴────────────────────────────────────┴─────────────┘
```

### Path interaction (canvas)

| Gesture | Behaviour |
|---------|-----------|
| **Single click** on a node | Highlight **upstream** path (predecessors + edges) with neon glow and animated particles on edges; other nodes dimmed |
| **Double click** on a node | **Focus mode**: hide nodes outside the full parcours (upstream + downstream; triggers use branch-aware logic) |
| **Click canvas** or **Show all** | Clear highlight and focus |

Active edges use custom `FlowNeonEdge` (glow, arrow marker, `animateMotion` particle). Reference edges stay purple when active.

### Edge styles

| `edgeKind` | Appearance | Meaning |
|------------|------------|---------|
| `flow` (default) | Solid gray (`#525252`); yellow when trace-highlighted | Structure from YAML (root → triggers → conditions → actions) |
| `reference` | Dashed purple (`#a78bfa`) | Trigger id used by a condition (focus + visual hint) |


| Region          | Width / height      | Role                                           |
| --------------- | ------------------- | ---------------------------------------------- |
| Header          | `py-2`, full width  | Brand, Local / HA mode, export/save            |
| Left sidebar    | `w-56`              | File/repo explorer or HA entity list           |
| Canvas          | `flex-1`, `min-h-0` | Pan/zoom graph                                 |
| Right inspector | `w-72`              | Selected node fields, blueprint preview inputs |
| Trace bar       | `h-36`              | Step list + import trace (local)               |


Use `flex`, `min-h-0`, and `overflow-hidden` on columns so Vue Flow scrolls correctly inside `h-screen`.

### Header

- App title: `text-lg font-semibold text-emerald-400` — primary brand accent.
- Mode switcher: pill on `bg-neutral-900`; active segment `bg-neutral-700`.
- Document title: `text-sm text-neutral-400`; dirty indicator `text-amber-400` (`•`).
- Primary actions: neutral buttons (`bg-neutral-800`); destructive/save-to-HA uses `bg-emerald-800`.

### Responsive behavior (M0)

Optimized for **desktop** (≥1024px). Narrow viewports may scroll horizontally; dedicated mobile layout is out of scope until requested.

---

## Color palette

### Surfaces


| Token (UnoCSS) | Usage                                   |
| -------------- | --------------------------------------- |
| `neutral-950`  | App background (implicit / body)        |
| `neutral-900`  | Panels, inactive controls               |
| `neutral-800`  | Borders (`border-neutral-800`), buttons |
| `neutral-700`  | Hover states, active tab segment        |
| `neutral-400`  | Secondary text, handles                 |
| `neutral-300`  | Node subtitle text                      |


### Brand and status


| Token                         | Usage                           |
| ----------------------------- | ------------------------------- |
| `emerald-400`                 | App title, active tab underline |
| `emerald-800` / `emerald-700` | Save to HA button               |
| `amber-400`                   | Unsaved (dirty) indicator       |
| `amber-500` / `amber-950`     | Trigger nodes                   |
| `red-950` / `red-300`         | Parse error banner              |


### Node kinds (graph)

Defined in `FlowNode.vue` — keep in sync when adding `FlowNodeKind` values:


| Kind             | Border               | Background       |
| ---------------- | -------------------- | ---------------- |
| `trigger`        | `border-amber-500`   | `bg-amber-950`   |
| `condition`      | `border-blue-500`    | `bg-blue-950`    |
| `action`         | `border-emerald-500` | `bg-emerald-950` |
| `choose`         | `border-purple-500`  | `bg-purple-950`  |
| `variables`      | `border-cyan-500`    | `bg-cyan-950`    |
| `blueprint_meta` | `border-pink-500`    | `bg-pink-950`    |
| `root`           | `border-neutral-500` | `bg-neutral-900` |
| default          | `border-neutral-600` | `bg-neutral-900` |


### Trace highlight

Executed nodes during trace playback:

- `ring-2 ring-yellow-400 ring-offset-2 ring-offset-neutral-950` on the node card.
- Non-executed nodes: no ring; optional future dimming (`opacity-60`) for branches not taken.

---

## Typography

- **Base:** system UI stack via Uno preset (Tailwind-compatible).
- **Node title:** `text-sm font-medium capitalize` (kind name), prefixed by a Lucide icon (`i-lucide-*`, 16px) mapped per `FlowNodeKind` in `FlowNode.vue`.
- **Node label:** `text-xs text-neutral-300` (truncation acceptable; full text in inspector).
- **Sidebar / tabs:** `text-xs` for density.
- **Inspector:** `text-sm` for labels and fields.

Avoid custom web fonts in M0 to keep the HA bundle small.

---

## Components

### Reka UI

Use Reka primitives for:

- **Tabs** — sidebar (`TabsRoot`, `TabsList`, `TabsTrigger`, `TabsContent`).
- **Labels** — inspector field labels (`Label`).
- **Future:** `Dialog`, `Select`, `Tooltip` for entity pickers and confirmations.

Style Reka parts with UnoCSS + `data-[state=active]:` attributes; do not fight Reka with heavy global CSS.

### Buttons

- Default: `rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700`.
- Disabled: `disabled:opacity-50` or native `:disabled` (prefer explicit disabled state).
- Primary (HA save): emerald variant (see header).

### Vue Flow

- Use default theme CSS imports in `main.ts`.
- Custom node type: `FlowNode` only for M0.
- Handles: `!bg-neutral-400`, left target / right source.
- Background grid: `@vue-flow/background` (subtle; do not overpower nodes).
- Controls: `@vue-flow/controls` bottom-right if present.

### Icons

- **UnoCSS preset-icons** with **Lucide** (`i-lucide-`* classes).
- Icon size: align with `text-sm` / `text-base`; do not mix icon families.

---

## Interaction patterns


| Action            | Pattern                                                         |
| ----------------- | --------------------------------------------------------------- |
| Select node       | Click node → inspector populates; store `selectedNodeId`        |
| Edit node         | Inspector fields → `store.updateSelectedNodeData`               |
| Blueprint preview | Inspector inputs → `store.previewInputs` + reload               |
| Load file         | Sidebar repo list / file picker / paste                         |
| Export YAML       | Header “Export YAML”; filename from source                      |
| Trace             | Timeline click or import JSON → `traceOverlay` + node highlight |
| Pan/zoom          | Vue Flow defaults; no custom gesture overrides in M0            |


Feedback:

- Parse errors: full-width banner under header (`bg-red-950`, `text-red-300`).
- Invalid JSON in inspector: silent fail on apply (future: inline error text).

---

## Modes: Local vs Home Assistant


| Aspect     | Local                  | HA panel                         |
| ---------- | ---------------------- | -------------------------------- |
| Sidebar    | Repo + file + paste    | Automations / scripts list       |
| Save       | Download YAML          | “Save to HA” (emerald)           |
| Trace      | Paste JSON             | WebSocket trace list             |
| Connection | Optional `VITE_HA_URL` | `window.hassUrl` / embedded auth |


Mode toggle disabled for HA when not connected in standalone dev — use `disabled` + neutral styling, not hidden.

---

## Accessibility

- Prefer **Reka** components for focus management and keyboard support.
- Interactive elements: visible focus (add `focus-visible:ring-2 focus-visible:ring-emerald-500` when touching buttons/links).
- Color is not the only cue: node cards show **kind** text plus **label**.
- Contrast: keep text at `neutral-300` minimum on `*-950` backgrounds.

---

## Do / Don’t


| Do                                        | Don’t                                         |
| ----------------------------------------- | --------------------------------------------- |
| Use Uno utility classes in templates      | Add large SCSS/Less layers                    |
| Extend semantic node colors for new kinds | Random per-node colors                        |
| Keep graph readable at default zoom       | Oversized nodes or fonts                      |
| Match emerald accent for brand actions    | Introduce a second brand color without reason |
| Document new patterns in this file        | One-off styles only in a single component     |


---

## Future UI work (roadmap alignment)

- **Entity / service pickers** — Reka `Combobox` or HA-style entity picker; reuse HA colors.
- **Simulation** — mock state banner + highlighted “would-run” path (distinct from trace yellow).
- **Breakpoints** — debug UI tied to `trace/debug/`*; use purple accent sparingly for debug-only chrome.
- **Light theme** — optional via CSS variables if HA panel requires it; dark remains default.

When implementing these, update this document and `flow-ui/uno.config.ts` if new tokens or shortcuts are added.