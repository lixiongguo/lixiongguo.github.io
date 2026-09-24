'use strict';
// ============================================================
//  Node 复现脚本：复刻 uv-unwrap-simple.html 里喂给 wasm 的数据
//    normalizeObject  ->  p/maxDim - center
//    collectMeshData  ->  按 Math.round(x*1e5) 合并顶点（会造出退化面）
//    repairMeshForSolver -> 页面当前的“丢弃规则”
// 用法:
//   node run_lscm.js <model.obj> [--sanitized] [--no-repair] [--module <glue.js>]
// ============================================================
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const objPath = argv[0];
const forceSanitized = argv.includes('--sanitized');
const noRepair = argv.includes('--no-repair');
const modArg = argv.indexOf('--module');
const gluePath = modArg >= 0 ? argv[modArg + 1] : path.join(__dirname, 'uv_unwrap_simple_dbg.js');

if (!objPath) { console.error('usage: node run_lscm.js <model.obj> [--sanitized] [--no-repair]'); process.exit(2); }

// ---------- 1. OBJ 解析（只取 v / f） ----------
function parseObj(text) {
  const v = [];
  const f = [];
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (t.charCodeAt(0) === 118 /* v */ && t[1] === ' ') {          // "v x y z"
      const p = t.split(/\s+/);
      v.push([parseFloat(p[1]), parseFloat(p[2]), parseFloat(p[3])]);
    } else if (t.charCodeAt(0) === 102 /* f */ && t[1] === ' ') {   // "f a//b c//d e//f"
      const parts = t.split(/\s+/).slice(1);
      const idx = [];
      for (const s of parts) {
        const n = parseInt(s.split('/')[0], 10);
        if (!isNaN(n)) idx.push(n - 1);
      }
      if (idx.length >= 3) f.push(idx);
    }
  }
  return { v, f };
}

// ---------- 2. normalizeObject（three.js: position=-center, scale=1/maxDim -> p/maxDim - center） ----------
function buildTransform(v, f, out) {
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  const used = new Uint8Array(v.length);
  for (const face of f) for (const i of face) if (i >= 0 && i < v.length) used[i] = 1;
  for (let i = 0; i < v.length; i++) {
    if (!used[i]) continue;
    const p = v[i];
    if (p[0] < minX) minX = p[0]; if (p[0] > maxX) maxX = p[0];
    if (p[1] < minY) minY = p[1]; if (p[1] > maxY) maxY = p[1];
    if (p[2] < minZ) minZ = p[2]; if (p[2] > maxZ) maxZ = p[2];
  }
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2, cz = (minZ + maxZ) / 2;
  const maxDim = Math.max(maxX - minX, maxY - minY, maxZ - minZ) || 1;
  const s = 1 / maxDim;
  out.count = v.length;
  out.pos = new Float64Array(v.length * 3);
  for (let i = 0; i < v.length; i++) {
    out.pos[i * 3]     = v[i][0] * s - cx;
    out.pos[i * 3 + 1] = v[i][1] * s - cy;
    out.pos[i * 3 + 2] = v[i][2] * s - cz;
  }
  return { maxDim, center: [cx, cy, cz], pos: out.pos };
}

// ---------- 3. collectMeshData（按 1e-5 网格合并） ----------
function collect(tr, f) {
  const vertexMap = new Map();
  const positions = [];
  const faces = [];
  function getVertexIndex(x, y, z) {
    const key = [Math.round(x * 100000), Math.round(y * 100000), Math.round(z * 100000)].join('_');
    if (!vertexMap.has(key)) { vertexMap.set(key, positions.length); positions.push([x, y, z]); }
    return vertexMap.get(key);
  }
  const loc = new Array(16);
  for (const face of f) {
    const n = face.length;
    for (let k = 0; k < n; k++) {
      const b = face[k] * 3;
      loc[k] = getVertexIndex(tr.pos[b], tr.pos[b + 1], tr.pos[b + 2]);
    }
    for (let k = 1; k + 1 < n; k++) faces.push([loc[0], loc[k], loc[k + 1]]);  // 扇形三角化
  }
  return { positions, faces };
}

// ---------- 4. repairMeshForSolver（语义等价，findNonManifoldVertex 用邻接表加速） ----------
function repair(meshData) {
  const data = { positions: meshData.positions.map(p => [p[0], p[1], p[2]]), faces: [] };
  let droppedDegenerate = 0, droppedOutOfRange = 0;
  for (const f of meshData.faces) {
    if (f.length < 3) continue;
    if (f[0] === f[1] || f[1] === f[2] || f[2] === f[0]) { droppedDegenerate++; continue; }
    if (f[0] < 0 || f[1] < 0 || f[2] < 0) { droppedOutOfRange++; continue; }
    if (f[0] >= data.positions.length || f[1] >= data.positions.length || f[2] >= data.positions.length) { droppedOutOfRange++; continue; }
    data.faces.push([f[0], f[1], f[2]]);
  }

  let edgeSplits = 0, vertexSplits = 0;
  const edgeKey = (a, b) => (a < b ? a + '_' + b : b + '_' + a);
  function buildEdgeFaces() {
    const edges = new Map();
    for (let fi = 0; fi < data.faces.length; fi++) {
      const f = data.faces[fi];
      for (const e of [[f[0], f[1]], [f[1], f[2]], [f[2], f[0]]]) {
        const k = edgeKey(e[0], e[1]);
        let info = edges.get(k);
        if (!info) { info = { a: Math.min(e[0], e[1]), b: Math.max(e[0], e[1]), faces: [] }; edges.set(k, info); }
        info.faces.push(fi);
      }
    }
    return edges;
  }
  function splitNonManifoldEdges() {
    let changed = false;
    buildEdgeFaces().forEach(function (info) {
      if (info.faces.length <= 2) return;
      for (let i = 2; i < info.faces.length; i++) {
        const fi = info.faces[i], f = data.faces[fi];
        const na = data.positions.length;
        data.positions.push(data.positions[info.a].slice());
        const nb = data.positions.length;
        data.positions.push(data.positions[info.b].slice());
        data.faces[fi] = f.map(v => (v === info.a ? na : (v === info.b ? nb : v)));
        edgeSplits++;
        changed = true;
      }
    });
    return changed;
  }
  // 顶点 -> 关联面；面-面相邻判定与原实现一致（在该顶点处共边）
  function buildVertexFaces() {
    const vf = new Map();
    for (let fi = 0; fi < data.faces.length; fi++) {
      const f = data.faces[fi];
      for (const v of f) {
        let arr = vf.get(v);
        if (!arr) { arr = []; vf.set(v, arr); }
        arr.push(fi);
      }
    }
    return vf;
  }
  function findNonManifoldVertex(vf) {
    for (const [v, incident] of vf) {
      if (incident.length <= 1) continue;
      const adj = new Map();
      for (const fi of incident) adj.set(fi, new Set());
      for (let i = 0; i < incident.length; i++) {
        const fi = incident[i], f = data.faces[fi];
        const others = f.filter(x => x !== v);
        for (let j = i + 1; j < incident.length; j++) {
          const fj = incident[j], f2 = data.faces[fj];
          const shared = f2.filter(x => x !== v);
          if (others.some(u => shared.indexOf(u) >= 0)) { adj.get(fi).add(fj); adj.get(fj).add(fi); }
        }
      }
      const seen = new Set([incident[0]]), stack = [incident[0]];
      while (stack.length) {
        const cur = stack.pop();
        for (const nb of adj.get(cur) || []) if (!seen.has(nb)) { seen.add(nb); stack.push(nb); }
      }
      if (seen.size !== incident.length) return v;
    }
    return -1;
  }
  function splitNonManifoldVertex(v) {
    const incident = [];
    for (let fi = 0; fi < data.faces.length; fi++) {
      const f = data.faces[fi];
      if (f[0] === v || f[1] === v || f[2] === v) incident.push(fi);
    }
    const adj = new Map();
    for (const fi of incident) adj.set(fi, new Set());
    for (let i = 0; i < incident.length; i++) {
      const fi = incident[i], f = data.faces[fi], others = f.filter(x => x !== v);
      for (let j = i + 1; j < incident.length; j++) {
        const fj = incident[j], f2 = data.faces[fj], shared = f2.filter(x => x !== v);
        if (others.some(u => shared.indexOf(u) >= 0)) { adj.get(fi).add(fj); adj.get(fj).add(fi); }
      }
    }
    const components = [], visited = new Set();
    for (const start of incident) {
      if (visited.has(start)) continue;
      const comp = [], stack = [start];
      visited.add(start);
      while (stack.length) {
        const cur = stack.pop();
        comp.push(cur);
        for (const nb of adj.get(cur) || []) if (!visited.has(nb)) { visited.add(nb); stack.push(nb); }
      }
      components.push(comp);
    }
    if (components.length <= 1) return false;
    for (let c = 1; c < components.length; c++) {
      const nv = data.positions.length;
      data.positions.push(data.positions[v].slice());
      for (const fi of components[c]) data.faces[fi] = data.faces[fi].map(x => (x === v ? nv : x));
      vertexSplits++;
    }
    return true;
  }
  for (let iter = 0; iter < 32; iter++) {
    const changedEdges = splitNonManifoldEdges();
    const vf = buildVertexFaces();
    const v = findNonManifoldVertex(vf);
    const changedVertex = v >= 0 ? splitNonManifoldVertex(v) : false;
    if (!changedEdges && !changedVertex) break;
  }
  return { meshData: data, edgeSplits, vertexSplits, droppedDegenerate, droppedOutOfRange };
}

function stats(positions, faces) {
  const deg = new Map();
  for (const f of faces) for (const e of [[f[0], f[1]], [f[1], f[2]], [f[2], f[0]]]) {
    const k = e[0] < e[1] ? e[0] + '_' + e[1] : e[1] + '_' + e[0];
    deg.set(k, (deg.get(k) || 0) + 1);
  }
  let nm = 0, selfLoop = 0;
  for (const [k, c] of deg) { if (c > 2) nm++; if (k.split('_')[0] === k.split('_')[1]) selfLoop++; }
  const used = new Uint8Array(positions.length);
  for (const f of faces) for (const v of f) used[v] = 1;
  let isolated = 0;
  for (let i = 0; i < used.length; i++) if (!used[i]) isolated++;
  return { edges: deg.size, nonManifoldEdges: nm, selfLoopEdges: selfLoop, isolatedVerts: isolated };
}

(async function main() {
  const text = fs.readFileSync(objPath, 'utf8');
  const raw = parseObj(text);
  const tr = buildTransform(raw.v, raw.f, {});
  const collected = collect(tr, raw.f);
  console.log('[obj]        v=%d f=%d  (+triangulated f=%d)', raw.v.length, raw.f.length, collected.faces.length);
  console.log('[collect]    dedup vertices=%d faces=%d  (合并掉 %d 个)', collected.positions.length, collected.faces.length,
              raw.v.length - collected.positions.length);
  const s0 = stats(collected.positions, collected.faces);
  console.log('[collected]  edges=%d nonManifold=%d selfLoop=%d isolated=%d', s0.edges, s0.nonManifoldEdges, s0.selfLoopEdges, s0.isolatedVerts);

  const rep = repair(collected);
  console.log('[repair]     edgeSplits=%d vertexSplits=%d droppedDegenerate=%d droppedOutOfRange=%d -> v=%d f=%d',
              rep.edgeSplits, rep.vertexSplits, rep.droppedDegenerate, rep.droppedOutOfRange,
              rep.meshData.positions.length, rep.meshData.faces.length);
  const s1 = stats(rep.meshData.positions, rep.meshData.faces);
  console.log('[sanitized]  edges=%d nonManifold=%d selfLoop=%d isolated=%d', s1.edges, s1.nonManifoldEdges, s1.selfLoopEdges, s1.isolatedVerts);

  const pageUsesRepair = (rep.edgeSplits > 0 || rep.vertexSplits > 0);
  let meshData = collected, which = 'collected(原样，页面当前行为)';
  if (noRepair) { meshData = collected; which = 'collected(--no-repair)'; }
  else if (forceSanitized || pageUsesRepair) { meshData = rep.meshData; which = 'sanitized(清洗后)'; }
  console.log('[feed]       送入 wasm: %s', which);

  const Module = await require(path.resolve(gluePath))();
  const nV = meshData.positions.length, nF = meshData.faces.length;
  const posArr = new Float64Array(nV * 3);
  for (let i = 0; i < nV; i++) { posArr[i*3] = meshData.positions[i][0]; posArr[i*3+1] = meshData.positions[i][1]; posArr[i*3+2] = meshData.positions[i][2]; }
  const faceArr = new Int32Array(nF * 3);
  for (let i = 0; i < nF; i++) { faceArr[i*3] = meshData.faces[i][0]; faceArr[i*3+1] = meshData.faces[i][1]; faceArr[i*3+2] = meshData.faces[i][2]; }

  const posPtr = Module._malloc(posArr.length * 8);
  for (let i = 0; i < posArr.length; i++) Module.setValue(posPtr + i * 8, posArr[i], 'double');
  const facePtr = Module._malloc(faceArr.length * 4);
  for (let i = 0; i < faceArr.length; i++) Module.setValue(facePtr + i * 4, faceArr[i], 'i32');

  let ret = null, err = null;
  try {
    ret = Module.ccall('solve_lscm', 'number',
      ['number','number','number','number','number','number'],
      [posPtr, posArr.length, facePtr, faceArr.length, 0, 0]);
    const uvSize = Module.ccall('get_uv_result_size', 'number', [], []);
    const uvPtr = Module.ccall('get_uv_result', 'number', [], []);
    const uv = [];
    for (let i = 0; i < uvSize; i++) uv.push(Module.getValue(uvPtr + i * 8, 'double'));
    let nan = 0, minU = Infinity, maxU = -Infinity, minV = Infinity, maxV = -Infinity;
    for (let i = 0; i + 1 < uv.length; i += 2) {
      const u = uv[i], v = uv[i + 1];
      if (!isFinite(u) || !isFinite(v)) { nan++; continue; }
      if (u < minU) minU = u; if (u > maxU) maxU = u;
      if (v < minV) minV = v; if (v > maxV) maxV = v;
    }
    const spread = (maxU - minU) >= 1e-12 || (maxV - minV) >= 1e-12;
    console.log('[wasm]       solve_lscm=%d  uvSize=%d (expect %d)  非有限值=%d  UV范围 u[%s,%s] v[%s,%s]  有效展开=%s  time=%.1fms',
                ret, uvSize, nV * 2, nan, minU.toFixed(4), maxU.toFixed(4), minV.toFixed(4), maxV.toFixed(4),
                spread ? 'yes' : 'NO', Module.ccall('get_last_time_ms', 'number', [], []));
    try {
      console.log('[mesh]       V=%d F=%d E=%d HE=%d boundaryLoops=%d isolatedVerts=%d',
                  Module.ccall('dbg_vertex_count','number',[],[]), Module.ccall('dbg_face_count','number',[],[]),
                  Module.ccall('dbg_edge_count','number',[],[]), Module.ccall('dbg_halfedge_count','number',[],[]),
                  Module.ccall('dbg_boundary_loops','number',[],[]), Module.ccall('dbg_isolated_vertices','number',[],[]));
    } catch (e) { /* 正式产物没有 dbg_* 导出 */ }
  } catch (e) {
    err = e;
  }

  try { Module._free(facePtr); } catch (e) { console.log('[free facePtr] 抛错:', e.message); }
  try { Module._free(posPtr); } catch (e) { console.log('[free posPtr]  抛错:', e.message); }
  if (err) {
    console.log('\n===== 复现 WASM 异常 =====');
    console.log(err && err.stack ? err.stack : String(err));
    process.exit(1);
  }
  console.log('\n[OK] 本次未触发异常');
})().catch(e => { console.error('harness error:', e); process.exit(3); });
