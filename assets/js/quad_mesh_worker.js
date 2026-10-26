/* Quad-meshing solver thread. Each stage is its own call so the page can
   terminate this worker and leave the pipeline immediately. */

function wasmURL(file) {
  return new URL("../wasm/" + file, self.location.href).href;
}

function readDoubles(inst, ptr, count) {
  const out = new Float64Array(count);
  if (!ptr || count <= 0) return out;
  if (inst.HEAPF64) {
    return new Float64Array(inst.HEAPF64.buffer, ptr, count).slice();
  }
  for (let i = 0; i < count; i++) out[i] = inst.getValue(ptr + i * 8, "double");
  return out;
}

function readInts(inst, ptr, count) {
  const out = new Int32Array(count);
  if (!ptr || count <= 0) return out;
  if (inst.HEAP32) {
    return new Int32Array(inst.HEAP32.buffer, ptr, count).slice();
  }
  for (let i = 0; i < count; i++) out[i] = inst.getValue(ptr + i * 4, "i32");
  return out;
}

function uploadMesh(inst, positions, faces, nVerts, nFaces) {
  const posPtr = inst.ccall("malloc", "number", ["number"], [nVerts * 3 * 8]);
  const facePtr = inst.ccall("malloc", "number", ["number"], [nFaces * 3 * 4]);
  if (!posPtr || !facePtr) throw new Error("内存不足");
  if (inst.HEAPF64) inst.HEAPF64.set(positions, posPtr / 8);
  else {
    for (let i = 0; i < positions.length; i++) inst.setValue(posPtr + i * 8, positions[i], "double");
  }
  if (inst.HEAP32) inst.HEAP32.set(faces, facePtr / 4);
  else {
    for (let i = 0; i < faces.length; i++) inst.setValue(facePtr + i * 4, faces[i], "i32");
  }
  return { posPtr: posPtr, facePtr: facePtr };
}

let naiveInst = null;
let fieldInst = null;

async function naiveModule() {
  if (naiveInst) return naiveInst;
  importScripts(wasmURL("naive_quad.js"));
  naiveInst = await self.NaiveQuadMerge({ locateFile: wasmURL });
  return naiveInst;
}

async function fieldModule() {
  if (fieldInst) return fieldInst;
  importScripts(wasmURL("uv_unwrap_field.js"));
  fieldInst = await self.UvUnwrapFieldSolver({ locateFile: wasmURL });
  return fieldInst;
}

function postStage(index, state, ms) {
  self.postMessage({ type: "stage", index: index, state: state, ms: ms || 0 });
}

async function runNaive(msg) {
  const inst = await naiveModule();
  const count = inst.ccall("naive_stage_count", "number", [], []);
  const names = [];
  for (let i = 0; i < count; i++) {
    names.push(inst.ccall("naive_stage_name", "string", ["number"], [i]) || ("阶段 " + (i + 1)));
  }
  self.postMessage({ type: "plan", names: names });
  for (let i = 0; i < names.length; i++) postStage(i, "run", 0);

  const mesh = uploadMesh(inst, msg.positions, msg.faces, msg.nVerts, msg.nFaces);
  const rc = inst.ccall("merge_tris_to_quads", "number", ["number", "number", "number", "number"],
    [mesh.posPtr, msg.nVerts, mesh.facePtr, msg.nFaces]);
  inst.ccall("free", "void", ["number"], [mesh.posPtr]);
  inst.ccall("free", "void", ["number"], [mesh.facePtr]);
  if (rc !== 0) throw new Error("合并失败 " + rc);

  const recorded = inst.ccall("get_stage_count", "number", [], []);
  for (let i = 0; i < names.length; i++) {
    const ms = i < recorded ? inst.ccall("get_stage_ms", "number", ["number"], [i]) : 0;
    postStage(i, "done", ms);
  }
  const quadCount = inst.ccall("get_quad_count", "number", [], []);
  const leftCount = inst.ccall("get_leftover_count", "number", [], []);
  const quads = readInts(inst, inst.ccall("get_quads", "number", [], []), quadCount * 4);
  const leftovers = readInts(inst, inst.ccall("get_leftovers", "number", [], []), leftCount * 3);
  self.postMessage({
    type: "result",
    algo: "naive",
    quads: quads,
    leftovers: leftovers
  }, [quads.buffer, leftovers.buffer]);
}

async function runField(msg) {
  const inst = await fieldModule();
  const mesh = uploadMesh(inst, msg.positions, msg.faces, msg.nVerts, msg.nFaces);
  const loaded = inst.ccall("load_mesh", "number", ["number", "number", "number", "number"],
    [mesh.posPtr, msg.positions.length, mesh.facePtr, msg.faces.length]);
  inst.ccall("free", "void", ["number"], [mesh.posPtr]);
  inst.ccall("free", "void", ["number"], [mesh.facePtr]);
  if (loaded !== 0) throw new Error("网格加载失败");

  const algoId = msg.algo === "quadcover" ? 1 : 0;
  const count = inst.ccall("field_prepare", "number", ["number"], [algoId]);
  if (count < 0) throw new Error("流水线未能开始");
  const names = [];
  for (let i = 0; i < count; i++) {
    names.push(inst.ccall("field_stage_name", "string", ["number"], [i]) || ("阶段 " + (i + 1)));
  }
  self.postMessage({ type: "plan", names: names });

  for (let i = 0; i < count; i++) {
    postStage(i, "run", 0);
    const rc = inst.ccall("field_run_stage", "number", ["number"], [i]);
    if (rc === 2) {
      postStage(i, "skip", 0);
      continue;
    }
    if (rc !== 0) {
      postStage(i, "fail", 0);
      throw new Error(names[i] + " 失败");
    }
    const recorded = inst.ccall("field_recorded_count", "number", [], []);
    const ms = recorded > 0 ? inst.ccall("field_recorded_ms", "number", ["number"], [recorded - 1]) : 0;
    postStage(i, "done", ms);
    if (msg.algo === "miq" && i === 2) {
      const nFaces = inst.ccall("field_capture_cross", "number", [], []);
      if (nFaces > 0) {
        const dirs = readDoubles(inst, inst.ccall("get_cross_preview", "number", [], []), nFaces * 6);
        const nEdges = inst.ccall("get_cross_edge_count", "number", [], []);
        const edges = readInts(inst, inst.ccall("get_cross_edges", "number", [], []), nEdges * 3);
        const nSing = inst.ccall("get_singular_count", "number", [], []);
        const singulars = readInts(inst, inst.ccall("get_singular_verts", "number", [], []), nSing);
        self.postMessage({
          type: "preview",
          kind: "cross",
          dirs: dirs,
          edges: edges,
          singulars: singulars
        }, [dirs.buffer, edges.buffer, singulars.buffer]);
      }
    }
  }

  const finished = inst.ccall("field_finish", "number", [], []);
  if (finished !== 0) throw new Error("结果写回失败");
  const uvCount = inst.ccall("get_uv_result_size", "number", [], []);
  const uv = readDoubles(inst, inst.ccall("get_uv_result", "number", [], []), uvCount);
  const cornerCount = inst.ccall("get_corner_uv_size", "number", [], []);
  const corners = readDoubles(inst, inst.ccall("get_corner_uv", "number", [], []), cornerCount);
  inst.ccall("dispose", "void", [], []);
  const transfers = [uv.buffer];
  if (corners.buffer !== uv.buffer) transfers.push(corners.buffer);
  self.postMessage({
    type: "result",
    algo: msg.algo,
    uv: uv,
    corners: corners
  }, transfers);
}

self.onmessage = function (event) {
  const msg = event.data;
  if (!msg || msg.type !== "run") return;
  const job = msg.algo === "naive" ? runNaive(msg) : runField(msg);
  job.catch(function (error) {
    self.postMessage({ type: "error", message: error && error.message ? error.message : String(error) });
  });
};
