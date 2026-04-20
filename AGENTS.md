# Agent instructions — Mirabelle HA Blueprints

This file is the primary guide for AI coding agents working in this repository. It consolidates the former Cursor rules under `.cursor/rules/` and reflects the actual project layout and workflows.

## Project purpose

**Mirabelle HA Blueprints** is a monorepo for:

- **Home Assistant blueprints** (`blueprints/automations/`, `blueprints/scripts/`) published for import via GitHub / my.home-assistant.io.
- **Optional tooling** in `scripts/` (TypeScript + Node) to install blueprints and update automations against a live HA instance.
- **HACS-oriented custom integrations** under `packages/`*, synced to **dedicated GitHub repositories** for HACS (see `.github/MONOREPO_SYNC.md` and workflow files under `.github/workflows/`).

**Target platform:** Home Assistant **2025.5.3** or later (pin or raise this when HA APIs or blueprint semantics change).

**Human language vs. repo language:** Chat and issues may be in French; **all repository text intended for users** (blueprint names/descriptions where shown in HA, Markdown under `docs/`, English `README`s in packages) must be **English** unless an existing artifact is explicitly localized (e.g. translation JSON files).

---

## Repository layout (authoritative)

```
mirabelle-ha-blueprints/
├── AGENTS.md                 ← this file
├── README.md                 ← user-facing overview and import links
├── TODO.md                   ← informal backlog
├── blueprints/
│   ├── automations/          ← automation blueprints (*.yaml)
│   └── scripts/              ← script blueprints (*.yaml)
├── docs/                     ← English documentation per blueprint/feature
├── scripts/                  ← Node/TS utilities (pnpm scripts)
├── templates/                ← e.g. cover template helpers
├── packages/
│   ├── cover-manager/        ← HACS integration (synced to sub-repo)
│   ├── imeon_energy_api/    ← HACS integration (synced to sub-repo)
│   └── cast-bridge/         ← auxiliary / experimental tooling (not a pnpm workspace member)
├── .github/workflows/       ← CI, release, monorepo → HACS sync
└── .cursor/rules/           ← legacy Cursor rule files (kept for editor; AGENTS.md is canonical for agents)
```

**Note:** Older rule text mentioned `scenes/` and `dashboards/` under `blueprints/` — they are part of the **intended** layout and are referenced by install scripts; add those directories when you add blueprints of those types.

---

## Blueprints (`blueprints/**/*.yaml`)

### Naming and branding

- Every blueprint **name** must start with `**[CDA]`** (Chatondearu).
- Prefer a short **emoji** in the visible name after `[CDA]` for quick recognition (e.g. `[CDA] 🔔 Scheduled Bell Sound`).
- **Filenames:** `kebab-case.yaml`.

### Structure and quality

- Valid YAML; follow [Home Assistant blueprint](https://www.home-assistant.io/docs/automation/using_blueprints/) conventions.
- Required top-level concepts: `blueprint` → at least `**name`**, `**domain`** (`automation` or `script`), sensible `**input**` with `**selector**` where appropriate.
- Include `**mode**` for automations where relevant (`single`, `restart`, `queued`, `parallel`).
- Prefer **optional triggers** via an `input` list (e.g. `object` / `multiple` triggers) when it improves reuse.
- Use `**!input`** for parameters; avoid hard-coding secrets; document external dependencies (entities, integrations, scripts).
- Keep actions **readable**; add **English comments** only for non-obvious logic.
- **Security:** no tokens, passwords, or private URLs in committed YAML.

### Selectors (common)

Use appropriate `selector` types: `entity`, `text`, `number`, `boolean`, `select`, `time`, `target`, `object` (e.g. for flexible trigger definitions).

---

## Documentation (`docs/**/*.md` and package READMEs)

- **Language:** English only for `docs/` and root `README.md`.
- **Filenames:** `kebab-case.md`.
- Per-blueprint docs should cover: purpose, prerequisites, installation (import URL), parameters (table or list), usage examples, troubleshooting, changelog when meaningful.
- **Markdown:** fenced code blocks with language tags; tables OK for parameters.
- When adding or renaming a blueprint, update `**README.md`** import URLs and the **docs** section if the blueprint is user-facing.

---

## Node / pnpm workspace

- **Package manager:** `pnpm` (see `packageManager` in root `package.json`).
- **Workspaces:** `packages/`* (`@mirabelle/cover-manager`, `@mirabelle/imeon-energy-api`, etc.).
- **Root scripts (examples):**
  - `pnpm run install-blueprints` — generates/uses HA API to install blueprints (requires `.env`).
  - `pnpm run update-automations` — updates automations on HA that match repo blueprints.
  - `pnpm run test-connection` — verifies HA connectivity.
- **Environment:** copy `.env.example` to `.env`; set `HA_URL`, `HA_TOKEN` (long-lived access token). Scripts default `HA_URL` to `http://supervisor/core` where applicable.
- **Scope of automation scripts:** typically only entities/blueprints whose names start with `[CDA]` — keep that contract when extending scripts.

---

## Python / HACS packages (`packages/`*)

- Custom integrations live under each package’s `custom_components/<domain>/`.
- Each HACS-eligible package should have `hacs.json`, `README.md`, and install docs as needed.
- **Do not edit the public HACS sub-repositories directly** — they are mirrors; change the monorepo and let sync workflows update them (see `.github/MONOREPO_SYNC.md`).
- `**packages/cast-bridge`:** treated as auxiliary (Nix/Python); not wired into root `pnpm` workspaces — follow any existing `Blueprint.md` / local docs in that folder when touching it.

---

## CI and validation (`.github/workflows`)

- `**validate.yml`:** on PRs/pushes to `main` — installs `homeassistant`, runs `yamllint` on `blueprints/**/*.yaml`, `hass --script check_config`, and a **Python structural check** that every `blueprints/**/*.yaml` file loads as YAML (with `!input` / `!secret` stripped) and contains a `blueprint` section with `name` and `domain`.
- `**release.yml`:** on tags `v`* — creates a GitHub Release.
- **Sync workflows:** e.g. `sync-cover-manager.yml`, `sync-imeon-energy-api.yml` — push selected `packages/<name>/`** to separate repos; require `RELEASE_TOKEN` secret where documented.

Agents should ensure new blueprints **pass** the structural validation script and avoid YAML that breaks `yaml.safe_load` after the tag substitution used in CI.

---

## Versioning, commits, and git workflow

- **Semantic versioning** for releases; Git tags `v`* drive GitHub Releases.
- **Conventional Commits**, enforced by **commitlint** (`commitlint.config.js`): types include `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`.
- **Scope is required** (`scope-empty`: never). Use a lowercase scope such as `blueprints`, `docs`, `ci`, `cover-manager`, `imeon`, `scripts`, etc.
- Example: `feat(blueprints): add optional mqtt trigger to scheduled bell sound`

**Project rule (from legacy `.cursor/rules`):** after substantive edits to blueprints, docs, or automation-related config, **commit with a clear message** and **push** to keep the remote history aligned. Agents with git access should follow this unless the user explicitly asks otherwise.

---

## Testing expectations

- Blueprints: validate in a **clean HA** context when possible; exercise parameters and edge cases; align with the **declared minimum HA version**.
- Integrations: follow each package’s patterns (`pytest`/HA guidelines as applicable).
- Prefer running `**pnpm run validate`** locally before pushing when Node/pnpm is available.

---

## Security and privacy

- Never commit secrets, tokens, or instance-specific URLs in YAML, Markdown, or scripts.
- Document security-relevant choices (e.g. webhooks, network access) in English in `docs/` or package READMEs.

---

## Quick checklist for agents


| Task                       | Check                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------ |
| New/changed blueprint      | `[CDA]` prefix, English description, selectors + defaults, no secrets                |
| User docs                  | English in `docs/`, README links updated                                             |
| New HA integration package | `hacs.json`, manifest, sync workflow / sub-repo docs per `MONOREPO_SYNC.md`          |
| CI                         | YAML loads; blueprint block present; consider running root `pnpm`/`yamllint` locally |
| Commit                     | Conventional commit **with scope**                                                   |


---

## Relationship to `.cursor/rules/*.mdc`

The files `.cursor/rules/project.mdc`, `blueprint.mdc`, and `documentation.mdc` summarized older editor-specific rules. `**AGENTS.md` is the canonical instructions file for coding agents.** Keep `.mdc` files aligned when they materially diverge, or consolidate future edits here first.