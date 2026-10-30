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

if [[ "$(uname -s)" == "Linux" ]]; then
  CXX="${CXX:-g++}"
else
  CXX="${CXX:-clang++}"
fi
MODE="${1:-release}"

# GLFW3 for the Linux/WSL viewer: prefer a system install, fall back to the
# per-user copy under ~/.local/glfw (no sudo required).
GLFW_CFLAGS=""
GLFW_LIBS=""
if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists glfw3; then
  GLFW_CFLAGS="$(pkg-config --cflags glfw3)"
  GLFW_LIBS="$(pkg-config --libs glfw3)"
elif [[ -d "$HOME/.local/glfw/usr/include/GLFW" ]]; then
  GLFW_CFLAGS="-I$HOME/.local/glfw/usr/include"
  GLFW_LIBS="-L$HOME/.local/glfw/usr/lib/x86_64-linux-gnu -Wl,-rpath,$HOME/.local/glfw/usr/lib/x86_64-linux-gnu -lglfw"
else
  GLFW_LIBS="-lglfw"
fi

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

# Cross-platform viewer: GLFW + OpenGL + Dear ImGui (viewer_glfw.cpp).
build_viewer_linux() {
  local outdir="build/release"
  # ImGui 源码放在仓库外（MyDoc/deps/imgui_full），不进版本库
  local imgui=""
  for candidate in "../../../deps/imgui_full" "../deps/imgui_full" "../../deps/imgui_full"; do
    if [[ -d "$candidate" ]]; then imgui="$candidate"; break
    fi
  done
  if [[ -z "$imgui" ]]; then
    echo "找不到 imgui_full（期望 MyDoc/deps/imgui_full）" >&2
    exit 1
  fi
  mkdir -p "$outdir"
  echo "[build] viewer (glfw) -> ${outdir}/viewer"
  "$CXX" "${release_flags[@]}" \
    -I. -I "$imgui" -I "$imgui/backends" $GLFW_CFLAGS \
    -o "${outdir}/viewer" \
    viewer_glfw.cpp fluidsim.cpp levelset_util.cpp \
    "$imgui/imgui.cpp" "$imgui/imgui_draw.cpp" "$imgui/imgui_tables.cpp" \
    "$imgui/imgui_widgets.cpp" \
    "$imgui/backends/imgui_impl_glfw.cpp" "$imgui/backends/imgui_impl_opengl3.cpp" \
    $GLFW_LIBS -lGL -lX11 -ldl -lpthread
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
    if [[ "$(uname -s)" == "Linux" ]]; then build_viewer_linux; else build_viewer; fi
    ;;
  gui)
    if [[ "$(uname -s)" == "Linux" ]]; then build_viewer_linux; else build_viewer; fi
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
