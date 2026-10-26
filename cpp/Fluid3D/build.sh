#!/usr/bin/env bash
# Native Apple ARM64 build for the Fluid3D offline solver.
# The browser demo stays in wasm/ and is not built here.
#
#   ./build.sh            release solver -> build/release/solver
#   ./build.sh debug      debug solver   -> build/debug/solver
#   ./build.sh test       solver + 1 simulated frame into build/smoke/
#   ./build.sh run [dir]  solver, default 1000 frames
#   ./build.sh gui-build  viewer only    -> build/release/viewer
#   ./build.sh gui        build and open the viewer
set -euo pipefail

cd "$(dirname "$0")"

CXX="${CXX:-clang++}"
MODE="${1:-release}"

release_flags=(-std=c++17 -O3 -arch arm64 -mcpu=native)
debug_flags=(-std=c++17 -O0 -g -arch arm64)
if [[ "$(uname -m)" != "arm64" ]]; then
  release_flags=(-std=c++17 -O3 -march=native)
  debug_flags=(-std=c++17 -O0 -g)
fi

sources=(main.cpp fluidsim.cpp levelset_util.cpp)

build() {
  local kind="$1"
  local outdir="build/${kind}"
  mkdir -p "$outdir"
  local flags=()
  if [[ "$kind" == "debug" ]]; then
    flags=("${debug_flags[@]}")
  else
    flags=("${release_flags[@]}")
  fi
  echo "[build] $CXX ${flags[*]} -> ${outdir}/solver"
  "$CXX" "${flags[@]}" -I. -o "${outdir}/solver" "${sources[@]}"
  echo "[build] done: ${outdir}/solver"
}

build_viewer() {
  local outdir="build/release"
  mkdir -p "$outdir"
  echo "[build] viewer -> ${outdir}/viewer"
  "$CXX" "${release_flags[@]}" -fobjc-arc -framework Cocoa -I. \
    -o "${outdir}/viewer" viewer.mm ../resource_hud.mm fluidsim.cpp levelset_util.cpp
  echo "[build] done: ${outdir}/viewer"
}

case "$MODE" in
  release|build)
    build release
    ;;
  debug)
    build debug
    ;;
  test)
    build release
    mkdir -p build/smoke
    rm -f build/smoke/particles_*.txt
    echo "[test] 60^3 grid, 1 step"
    ./build/release/solver build/smoke/ 2
    python3 - <<'PY'
import pathlib
root = pathlib.Path("build/smoke")
for name in ("particles_0.txt", "particles_1.txt"):
    path = root / name
    lines = path.read_text().splitlines()
    if len(lines) < 2:
        raise SystemExit(f"{path} is empty")
    count, radius = lines[0].split()
    count = int(count)
    if count < 1 or len(lines) != count + 1:
        raise SystemExit(f"{path} header says {count} particles, file has {len(lines) - 1}")
    print(f"[test] ok {path} particles={count} radius={radius}")
PY
    ;;
  gui-build)
    build_viewer
    ;;
  gui)
    build_viewer
    echo "[gui] opening viewer"
    ./build/release/viewer
    ;;
  run)
    build release
    out="${2:-build/out/}"
    mkdir -p "$out"
    case "$out" in
      */) ;;
      *) out="${out}/" ;;
    esac
    echo "[run] 1000 frames -> $out"
    ./build/release/solver "$out"
    ;;
  *)
    echo "usage: ./build.sh [release|debug|test|run [outdir]|gui-build|gui]" >&2
    exit 2
    ;;
esac
