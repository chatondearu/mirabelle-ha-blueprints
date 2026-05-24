{
  description = "Mirabelle HA Blueprints — reproducible dev shell (Node, pnpm, Python, yamllint)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = false;
        };
        python = pkgs.python312;
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            nodejs_22
            corepack
            python
            python.pkgs.pip
            python.pkgs.virtualenv
            yamllint
            git
            bash
            jq
          ];

          shellHook = ''
            # Match package.json packageManager (pnpm@10.24.0)
            export COREPACK_ENABLE_STRICT=0
            corepack enable >/dev/null 2>&1 || true
            corepack prepare pnpm@10.24.0 --activate >/dev/null 2>&1 || true

            # Python venv for pytest-homeassistant-custom-component (pip pins in requirements-test.txt)
            if [ ! -d .venv ]; then
              echo "Creating .venv (Python test dependencies)..."
              ${python}/bin/python -m venv .venv
            fi
            # shellcheck disable=SC1091
            source .venv/bin/activate

            venv_marker=".venv/.deps-installed"
            if [ ! -f "$venv_marker" ] || [ requirements-test.txt -nt "$venv_marker" ]; then
              echo "Installing Python test dependencies from requirements-test.txt..."
              pip install -q -U pip wheel
              pip install -r requirements-test.txt
              touch "$venv_marker"
            fi

            export PYTHON="$PWD/.venv/bin/python"
            export PATH="$PWD/node_modules/.bin:$PATH"

            echo "Mirabelle HA Blueprints dev shell"
            echo "  node:   $(node --version 2>/dev/null || echo n/a)"
            echo "  pnpm:   $(pnpm --version 2>/dev/null || echo 'run: pnpm install')"
            echo "  python: $($PYTHON --version)"
            echo ""
            echo "  pnpm install          # Node workspace"
            echo "  pnpm run test:ha       # YAML + pytest (same as CI)"
            echo "  pnpm run dev:flow      # Mirabelle Flow UI"
          '';
        };
      });
}
