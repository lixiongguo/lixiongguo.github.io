#!/usr/bin/env bash
# Build WASM packages via package Makefile (conformal or Fluid3D)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -d "$SCRIPT_DIR/conformal-parameterization/wasm" ]]; then
  DEFAULT_MAKE_DIR="$SCRIPT_DIR/conformal-parameterization/wasm"
else
  DEFAULT_MAKE_DIR="$REPO_ROOT/../conformal-parameterization/wasm"
fi
MANIFEST="$SCRIPT_DIR/wasm_packages.yaml"

TARGET="${1:-page}"

resolve_pkg_field() {
  local name="$1" field="$2"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$name" "$field" "$MANIFEST" <<'PY'
import sys, yaml
from pathlib import Path
name, field, path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
pkg = (data.get("packages") or {}).get(name) or {}
print(pkg.get(field, "") or "")
PY
  else
    echo ""
  fi
}

resolve_make_target() {
  local name="$1"
  case "$name" in
    page|page-all) echo "build-page-all" ;;
    all) echo "build-all" ;;
    *) resolve_pkg_field "$name" "make_target" ;;
  esac
}

resolve_make_dir() {
  local name="$1"
  local rel
  rel="$(resolve_pkg_field "$name" "make_dir")"
  if [[ -n "$rel" ]]; then
    echo "$SCRIPT_DIR/$rel"
  else
    echo "$DEFAULT_MAKE_DIR"
  fi
}

MAKE_TARGET="$(resolve_make_target "$TARGET")"
if [[ -z "$MAKE_TARGET" ]]; then
  echo "Unknown target: $TARGET" >&2
  exit 1
fi

MAKE_DIR="$(resolve_make_dir "$TARGET")"

if ! command -v em++ >/dev/null 2>&1; then
  if [[ -f "$REPO_ROOT/cpp/emsdk/emsdk_env.sh" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/cpp/emsdk/emsdk_env.sh"
  fi
fi

echo "[build_wasm.sh] make -C $MAKE_DIR $MAKE_TARGET"
make -C "$MAKE_DIR" "$MAKE_TARGET"
