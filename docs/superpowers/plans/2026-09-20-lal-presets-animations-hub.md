# LAL Presets, Animations & Hub — Implementation Plan

> **For agentic workers:** Implement task-by-task. Tests deferred.

**Goal:** Add selectable profile presets (HA package helpers), pluggable light animations, then a lighting hub for shared profile mode.

**Architecture:** Companion package for presets; LAL resolves profile values from `local` or preset helpers; animation modifies brightness per lamp; hub only writes a global `input_select`.

**Tech Stack:** HA blueprints YAML, package helpers, English docs.

## Global Constraints

- HA 2025.5.3+; `[CDA]` prefix; English docs; no secrets; tests later.

## File map

| File | Role |
|------|------|
| `blueprints/scripts/create-lal-profile-presets.yaml` | Write preset package |
| `templates/…` or docs snippet | shell_command if needed (reuse existing LAL shell_command) |
| `blueprints/automations/living-area-adaptive-lighting.yaml` | Preset select + resolve + anim |
| `blueprints/automations/living-area-lighting-hub.yaml` | Global profile publisher |
| `blueprints/scripts/create-lal-hub-helpers.yaml` | Hub helpers |
| `docs/living-area-adaptive-lighting.md` | Docs |
| `docs/living-area-lighting-hub.md` | Hub docs |
| `README.md` | Links |

---

### Task 1: Preset companion + LAL preset resolution

- [ ] Script blueprint generating 3 presets of helpers
- [ ] LAL input `profile_preset` + templates reading helpers when not `local`
- [ ] Docs + validate

### Task 2: Animation engine

- [ ] `leaf_cloud` brightness modifier; wire into night (and mask)
- [ ] Docs

### Task 3: Hub

- [ ] Hub automation + helpers script
- [ ] LAL `follow_global_profile`
- [ ] Deploy to HA
