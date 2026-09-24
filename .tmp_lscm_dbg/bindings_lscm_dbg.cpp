// ============================================================
//  临时诊断模块：只保留 LSCM 路径
//  solve_lscm 的实现与 wasm/bindings_uv_unwrap_simple_compat.cpp 完全一致，
//  额外导出一组 dbg_* 用于查看 buildMesh 之后的网格规模。
// ============================================================
#include "Mesh.h"
#include "MeshIO.h"
#include "Lscm.h"
#include <chrono>
#include <vector>
#include <emscripten.h>

static Mesh*               g_mesh = nullptr;
static std::vector<double> g_uv;
static double              g_last_time = 0.0;

static bool buildMeshFrom(double* flatPos, int posLen, int* flatFace, int faceLen) {
    int nV = posLen / 3, nF = faceLen / 3;
    MeshData data;
    data.positions.reserve(nV);
    for (int i = 0; i < nV; ++i)
        data.positions.push_back(Eigen::Vector3d(flatPos[i*3], flatPos[i*3+1], flatPos[i*3+2]));
    data.indices.reserve(nF);
    for (int f = 0; f < nF; ++f) {
        data.indices.push_back({Index(flatFace[f*3], -1, -1),
                                Index(flatFace[f*3+1], -1, -1),
                                Index(flatFace[f*3+2], -1, -1)});
    }
    return MeshIO::buildMesh(data, *g_mesh);
}

static void extractUV() {
    g_uv.clear();
    for (auto& v : g_mesh->vertices) {
        g_uv.push_back(v.uv.x());
        g_uv.push_back(v.uv.y());
    }
}

static void recordTime(const std::chrono::steady_clock::time_point& t0) {
    auto t1 = std::chrono::steady_clock::now();
    g_last_time = std::chrono::duration<double, std::milli>(t1 - t0).count();
}

extern "C" {

EMSCRIPTEN_KEEPALIVE
void dispose() {
    if (g_mesh) { delete g_mesh; g_mesh = nullptr; }
    g_uv.clear();
    g_last_time = 0.0;
}

EMSCRIPTEN_KEEPALIVE
int solve_lscm(double* pos, int posLen, int* face, int faceLen, int /*a1*/, int /*a2*/) {
    dispose(); g_mesh = new Mesh();
    if (!buildMeshFrom(pos, posLen, face, faceLen)) return -4;
    Lscm lscm(*g_mesh);
    auto t0 = std::chrono::steady_clock::now();
    lscm.parameterize();
    recordTime(t0);
    if (!lscm.succeeded()) return -5;
    extractUV();
    return 0;
}

EMSCRIPTEN_KEEPALIVE
int get_uv_result_size() { return (int)g_uv.size(); }
EMSCRIPTEN_KEEPALIVE
double* get_uv_result() { return g_uv.data(); }
EMSCRIPTEN_KEEPALIVE
double get_last_time_ms() { return g_last_time; }

// ---------- 诊断辅助 ----------
EMSCRIPTEN_KEEPALIVE
int dbg_vertex_count()   { return g_mesh ? (int)g_mesh->vertices.size()   : -1; }
EMSCRIPTEN_KEEPALIVE
int dbg_face_count()     { return g_mesh ? (int)g_mesh->faces.size()      : -1; }
EMSCRIPTEN_KEEPALIVE
int dbg_edge_count()     { return g_mesh ? (int)g_mesh->edges.size()      : -1; }
EMSCRIPTEN_KEEPALIVE
int dbg_halfedge_count() { return g_mesh ? (int)g_mesh->halfEdges.size()  : -1; }
EMSCRIPTEN_KEEPALIVE
int dbg_boundary_loops() { return g_mesh ? (int)g_mesh->boundaries.size() : -1; }
EMSCRIPTEN_KEEPALIVE
int dbg_isolated_vertices() {
    if (!g_mesh) return -1;
    int n = 0;
    for (auto& v : g_mesh->vertices) if (v.isIsolated()) ++n;
    return n;
}

}
