#!/usr/bin/env bash
# Native Apple ARM64 (or the host arch) build for the MIS compare demo.
# The SFML previewer in src/main.cpp is not part of this target.
#
#   ./build.sh            release binary -> build/release/mis_compare
#   ./build.sh debug      debug binary   -> build/debug/mis_compare
#   ./build.sh test       release build + short render, checks the two PPMs differ
#   ./build.sh run        release build + default 480x360x64 into build/out
#   ./build.sh gui-build  compile the debug window only
#   ./build.sh gui        compile and open the debug window
set -euo pipefail

cd "$(dirname "$0")"

CXX="${CXX:-clang++}"
MODE="${1:-release}"
REPO_DEPS="../cpp/deps"

release_flags=(-std=c++17 -O3 -arch arm64 -mcpu=native)
debug_flags=(-std=c++17 -O0 -g -arch arm64)
host="$(uname -m)"
if [[ "$host" != "arm64" ]]; then
  release_flags=(-std=c++17 -O3 -march=native)
  debug_flags=(-std=c++17 -O0 -g)
fi

includes=(-I include -I "$REPO_DEPS")
common_sources=(
  src/image_stub.cpp
  src/renderer/path_tracing_renderer.cpp
  src/camera/camera.cpp
  src/camera/film.cpp
  src/camera/ray.cpp
  src/shape/sphere.cpp
  src/shape/plane.cpp
  src/shape/scene.cpp
  src/accelerate/scene_bvh.cpp
  src/accelerate/bounds.cpp
  src/material/diffuse_material.cpp
  src/material/specular_material.cpp
  src/material/ground_material.cpp
  src/light/area_light.cpp
  src/light/light_sampler.cpp
  src/sample/alias_table.cpp
  src/thread/thread_pool.cpp
  src/util/frame.cpp
)

compile_bin() {
  local kind="$1"
  local name="$2"
  shift 2
  local outdir="build/${kind}"
  mkdir -p "$outdir"
  local flags=()
  if [[ "$kind" == "debug" ]]; then
    flags=("${debug_flags[@]}")
  else
    flags=("${release_flags[@]}")
  fi
  echo "[build] $CXX ${flags[*]} -> ${outdir}/${name}"
  "$CXX" "${flags[@]}" "${includes[@]}" -o "${outdir}/${name}" "$@"
  echo "[build] done: ${outdir}/${name}"
}

build() {
  compile_bin "$1" mis_compare src/mis_compare.cpp "${common_sources[@]}"
}

build_gui() {
  compile_bin "$1" debug_gui -fobjc-arc -framework Cocoa \
    src/debug_gui.mm ../cpp/resource_hud.mm src/renderer/normal_renderer.cpp "${common_sources[@]}"
}

check_ppms() {
  python3 - "$1" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])

def load(name):
    path = root / name
    data = path.read_bytes()
    if not data.startswith(b"P6\n"):
        raise SystemExit(f"{path} is not a binary PPM")
    parts = data.split(b"\n", 3)
    if len(parts) != 4:
        raise SystemExit(f"{path} header is truncated")
    w, h = map(int, parts[1].split())
    if parts[2] != b"255":
        raise SystemExit(f"{path} max value is {parts[2]!r}")
    body = parts[3]
    if len(body) != w * h * 3:
        raise SystemExit(f"{path} pixel bytes {len(body)} != {w}*{h}*3")
    if not any(body):
        raise SystemExit(f"{path} is entirely black")
    return body

on = load("mis_on.ppm")
off = load("mis_off.ppm")
if on == off:
    raise SystemExit("MIS on and MIS off wrote the same image")
print(f"[test] ok {root}/mis_on.ppm and mis_off.ppm differ ({len(on)} bytes)")
PY
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
    echo "[test] 80x60 spp=4"
    (cd build/smoke && ../release/mis_compare 80 60 4)
    check_ppms build/smoke
    ;;
  run)
    build release
    mkdir -p build/out
    echo "[run] 480x360 spp=64 -> build/out"
    (cd build/out && ../release/mis_compare)
    ;;
  gui-build)
    build_gui release
    ;;
  gui)
    build_gui release
    echo "[gui] opening debug window"
    ./build/release/debug_gui
    ;;
  *)
    echo "usage: ./build.sh [release|debug|test|run|gui-build|gui]" >&2
    exit 2
    ;;
esac
