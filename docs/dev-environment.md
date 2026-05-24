# Development environment (Nix + direnv)

Reproducible tooling aligned with [CI](../.github/workflows/validate.yml): **Node.js 22**, **pnpm 10.24**, **Python 3.12**, and **yamllint**.

## Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled (`experimental-features = nix-command flakes` in `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`)
- [direnv](https://direnv.net/)
- [nix-direnv](https://github.com/nix-community/nix-direnv) (recommended; `.envrc` loads it automatically)

## Setup

```bash
cd /path/to/mirabelle-ha-blueprints
direnv allow
pnpm install
```

Entering the directory loads the flake dev shell: `node`, `pnpm`, `python`, and a project `.venv` with packages from [`requirements-test.txt`](../requirements-test.txt).

## Common commands

| Task | Command |
|------|---------|
| Full HA test suite (CI parity) | `pnpm run test:ha` |
| Mirabelle Flow UI | `pnpm run dev:flow` |
| Flow unit tests | `pnpm run test:flow` |
| Enter shell without direnv | `nix develop` |

## Without direnv

```bash
nix develop
pnpm install
pnpm run test:ha
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `direnv: command not found` | Install direnv and hook it into your shell (`direnv hook zsh` in `~/.zshrc`) |
| Flakes disabled | Add `experimental-features = nix-command flakes` to Nix config |
| Stale Python deps | `rm .venv/.deps-installed && direnv reload` |
| Skip pre-push tests | `SKIP_HA_TESTS=1 git push` (emergency only) |

Python packages are installed with **pip** inside `.venv` because `pytest-homeassistant-custom-component` pins a specific Home Assistant stack not provided by nixpkgs.
