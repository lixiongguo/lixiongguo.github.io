# LSCM 展开「内存越界」问题分析与修复记录

> 现象关键词：`camelhead_F22704.obj` + LSCM 展开 → 页面提示
> `WASM 内存越界（网格拓扑或数值异常）。已丢弃该实例，请重新点击「展开!」重试`
>
> **真实原因不是内存不够，而是 Eigen 把 91KB 临时数组分配到只有 64KB 的 wasm 栈上导致栈溢出**，
> 未开 `STACK_OVERFLOW_CHECK` 的产物把它表现为 `memory access out of bounds`。

- 记录日期：2026-09-24
- 影响范围：`assets/wasm/uv_unwrap_simple.js|wasm`（以及所有用 Eigen 稀疏 Cholesky 的 wasm 模块）
- 触发条件：未知量 `v = 2*(V-2) > 16384`（约 8K 顶点以上的网格）

---

## 1. 现象与复现条件

| 项目 | 内容 |
| --- | --- |
| 页面 | `uv-unwrap-simple.html`，算法选 LSCM，模型 `assets/Models/camelhead_F22704.obj` |
| 模型规模 | Vertices 11381 / Faces 22704（三角形，面格式 `f a//a b//b c//c`） |
| 复现条件 | **刷新页面后第一次操作就崩**（与"堆只涨不缩/累积内存"无关） |
| 控制台原文 | `memory access out of bounds`，页面 catch 后统一显示成"WASM 内存越界" |
| 其它模型 | assets/Models 中小模型正常，`hencky_F20000`（v≈20136）同样会崩 |

页面上的判定分支在 `uv-unwrap-simple.html:1336-1341`：

```js
if (msg.indexOf("memory access out of bounds") >= 0 || msg.indexOf("unreachable") >= 0) {
  wasmPoisoned = true;
  throw new Error("WASM 内存越界（网格拓扑或数值异常）。已丢弃该实例，请重新点击「展开!」重试");
}
```

即：这条提示同时对应"越界"和"abort"，**不能据此判断是内存不够**。

---

## 2. 排除"内存不够"

按当时的 `solveLeastSquares`（正规方程 + 直接 Cholesky）估算峰值：

| 量 | 规模 |
| --- | --- |
| `M`（`2F × 2(V-2)`，每面约 10 个非零） | ≈ 22.7 万非零 |
| `At = A.transpose()` | 同量级 |
| `At*A` | ≈ 110 万非零 |
| `SimplicialCholesky` 内部 `C`/`ap`/AMD 对称拷贝 + 因子 `L` 的 fill-in | 若干份 |

合计只有**几十 MB** 量级，而 wasm32 单实例上限 2GB，实跑时堆只涨到 **42MB**（见第 4 节日志），
因此"内存不够"这一诊断被排除，转向"非法访问 / 栈溢出"。

---

## 3. 排查过程

1. **静态排查 C++ 下标路径**：`Lscm::buildMassMatrix`（行/列越界 `return false`）、`Lscm::setUvs`（越界读保护）、
   `pinVertices` 的 pin 合法性校验、`MeshIO` 的容量预留（`nHE = 2*nE`，而实际创建数 `3F + E_bnd' = 2E`，精确匹配，
   不存在迭代器失效）——都带保护，无法解释该模型的崩溃。
2. **区分"旧产物"与"真 bug"**：CI 不构建 wasm（`.github/workflows/github-pages.yml` 只跑 `jekyll build` 后部署仓库），
   `assets/wasm/*` 是本地 em++ 产物，可能与当前源码不同步。故先用**当前源码**重建复现。
3. **构建带诊断信息的模块复现**（本机无 make/g++，用仓库自带 emsdk 的 `em++.bat`，Emscripten 5.0.6）：

```
cd cpp/conformal-parameterization/wasm
em++.bat -O1 -g -std=c++17 -I../../deps/eigen-3.4.0 -I../BaseMesh -I../Parameterization \
         -I../Parameterization/SimpleParam/LSCM ../../../.tmp_lscm_dbg/bindings_lscm_dbg.cpp \
         ../BaseMesh/Mesh.cpp ../BaseMesh/MeshIO.cpp ../BaseMesh/Vertex.cpp ../BaseMesh/Edge.cpp \
         ../BaseMesh/Face.cpp ../BaseMesh/HalfEdge.cpp ../Parameterization/Parameterization.cpp \
         ../Parameterization/SimpleParam/LSCM/Lscm.cpp \
         -o ../../../.tmp_lscm_dbg/uv_unwrap_simple_dbg.js \
         -sMODULARIZE=1 -sALLOW_MEMORY_GROWTH=1 -sWASM=1 \
         -sASSERTIONS=2 -sSAFE_HEAP=1 -sSTACK_OVERFLOW_CHECK=2 \
         "-sEXPORTED_FUNCTIONS=['_malloc','_free']" \
         "-sEXPORTED_RUNTIME_METHODS=['ccall','cwrap','getValue','setValue']" \
         -sEXPORT_NAME=UvUnwrapSimpleDbg
```

4. **Node 复现脚本**（`.tmp_lscm_dbg/run_lscm.js`）复刻页面前处理链，得到决定性栈帧：

```
Aborted(stack overflow (Attempt to set SP to 0x00000640,
         with stack limits [0x00006b60 - 0x00016b60]))
  at Eigen::SimplicialCholeskyBase<...>::analyzePattern_preordered(Eigen::SparseMatrix<double,0,int> const&, bool)
  at Eigen::SimplicialCholeskyBase<...>::compute<true>(...)
  at solveLeastSquares(...)
  at Lscm::parameterize()
  at solve_lscm
```

---

## 4. 根因

Eigen 的临时缓冲宏（`cpp/deps/eigen-3.4.0/Eigen/src/Core/util/Memory.h:592-598`）：

```cpp
#define ei_declare_aligned_stack_constructed_variable(TYPE,NAME,SIZE,BUFFER) \
  Eigen::internal::check_size_for_overflow<TYPE>(SIZE); \
  TYPE* NAME = (BUFFER)!=0 ? (BUFFER) \
             : reinterpret_cast<TYPE*>( \
                    (sizeof(TYPE)*SIZE<=EIGEN_STACK_ALLOCATION_LIMIT) ? EIGEN_ALIGNED_ALLOCA(sizeof(TYPE)*SIZE) \
                  : Eigen::internal::aligned_malloc(sizeof(TYPE)*SIZE) ); \
  ...
```

阈值默认 128KB（`Macros.h:576-579`：`#define EIGEN_STACK_ALLOCATION_LIMIT 131072`），
而 Emscripten 默认 **wasm 栈只有 64KB**。于是：

| 位置 | 栈上缓冲 | 本模型大小 | 是否走 alloca |
| --- | --- | --- | --- |
| `analyzePattern_preordered`（`SimplicialCholesky_impl.h:58`） | `Index tags[size]` | `4×22758 = 91032 B` | ✅ 90KB 上栈 → **溢出** |
| `factorize_preordered`（`SimplicialCholesky_impl.h:115-117`） | `pattern[size]`、`tags[size]` | 各 91032 B | ✅ 也会溢出 |
| 同上 | `Scalar y[size]` | `8×22758 = 182064 B` > 128KB | ❌ 走堆 |

- 未开 `STACK_OVERFLOW_CHECK` 时，alloca 越过栈底会写坏 wasm 线性内存，表现为栈帧里看到的
  `memory access out of bounds`；开启检查则直接报 `stack overflow (Attempt to set SP to ...)`。
- 判据：`4*(2(V-2)) > 65536` ⇒ **V ≳ 8.2K 顶点**（v > 16384）开始踩雷，
  所以只有 camelhead / hencky 这类较大模型崩，小模型正常。

---

## 5. 修复

### 5.1 构建参数（`cpp/conformal-parameterization/wasm/Makefile`）

```make
CXX       := em++
# EIGEN_STACK_ALLOCATION_LIMIT=0：置 0 后上述缓冲一律走 aligned_malloc，不再 alloca
CXXFLAGS  := -O3 -std=c++17 -Wall -Wextra -DEIGEN_STACK_ALLOCATION_LIMIT=0

EM_FLAGS  := --bind \
             -s MODULARIZE=1 \
             -s ALLOW_MEMORY_GROWTH=1 \
             -s WASM=1 \
             -s STACK_SIZE=1048576 \          # 1MB 栈兜底（原来是默认 64KB）
             ...

EM_FLAGS_COMPAT := -s MODULARIZE=1 \
             -s ALLOW_MEMORY_GROWTH=1 \
             -s WASM=1 \
             -s STACK_SIZE=1048576 \
             ...
```

说明：`EIGEN_STACK_ALLOCATION_LIMIT` 在 Eigen 里是 `#ifndef` 保护（`Macros.h:576`），
所以 `-D` 生效；置 0 后 `sizeof(TYPE)*SIZE <= 0` 恒为 false，全部改走 `aligned_malloc`，
配套的 `aligned_stack_memory_handler` 最后一个参数变为 `true`，会在作用域结束时正确 `free`，无双重释放问题。

### 5.2 重建产物

本机无 `make`，用与 Makefile 等价的 em++ 命令重建 `assets/wasm/uv_unwrap_simple.js|wasm`
（源文件列表见 Makefile 的 `SIMPLE_COMPAT_SRCS` / `SIMPLE_COMPAT_INC`；新增两个参数）。
重建前已备份原产物到 `.tmp_lscm_dbg/backup/`。

---

## 6. 验证

### 6.1 A/B 对照（同一模型，直接跑真实产物）

| 产物 | 结果 |
| --- | --- |
| 旧 `uv_unwrap_simple.wasm`（备份，默认 64KB 栈） | `RuntimeError: memory access out of bounds`（复现用户报错） |
| 新 `uv_unwrap_simple.wasm`（含修复） | `solve_lscm=0  uvSize=22762  非有限值=0  UV 范围 u[-0.9934,0.8968] v[-0.9045,0.9032]`，耗时 245~249 ms（两次运行） |

补充事实：新旧 `.js` glue **字节完全一致（MD5 相同）**，只有 `.wasm` 变化
⇒ 页面加载方式、导出 API 均不变，无兼容性风险，浏览器硬刷新即可生效。

### 6.2 回归（assets/Models 全量 11 个模型，新产物）

| 模型 | solve_lscm | uvSize | 非有限值 | 有效展开 | 耗时 |
| --- | --- | --- | --- | --- | --- |
| beetle_F2052 | 0 | 2566 | 0 | yes | 8.1 ms |
| bunnyhead_F3000 | 0 | 3100 | 0 | yes | 15.7 ms |
| **camelhead_F22704** | 0 | 22762 | 0 | yes | 248.5 ms |
| cathead_F248 | 0 | 262 | 0 | yes | 3.5 ms |
| hand_1_i_F4999 | 0 | 5034 | 0 | yes | 19.5 ms |
| hand_F3769 | 0 | 3810 | 0 | yes | 15.9 ms |
| hemi | 0 | 3970 | 0 | yes | 21.1 ms |
| hencky_F20000 | 0 | 20136 | 0 | yes | 149.0 ms |
| max_F3599 | 0 | 3734 | 0 | yes | 16.5 ms |
| Nefertiti_face | 0 | 598 | 0 | yes | 5.0 ms |
| spot_cowhead_F9024 | 0 | 9074 | 0 | yes | 67.7 ms |

（调试构建在有 `v=22758` 时曾打印 `Heap resize ... 35192832→42270720`，即堆峰值仅约 42MB，
再次印证与"内存不够"无关。）

---

## 7. 复现 / 回归命令

```powershell
cd c:\Users\lixio\OneDrive\Desktop\MyDoc\lixiongguo.github.io

# 单模型（可用 --module 指定产物，便于做 A/B）
node .tmp_lscm_dbg\run_lscm.js assets\Models\camelhead_F22704.obj --module assets\wasm\uv_unwrap_simple.js

# 旧产物对照
node .tmp_lscm_dbg\run_lscm.js assets\Models\camelhead_F22704.obj --module .tmp_lscm_dbg\backup\uv_unwrap_simple.js

# 全量回归
Get-ChildItem assets\Models\*.obj | Sort-Object Name | ForEach-Object {
  & node .tmp_lscm_dbg\run_lscm.js $_.FullName --module assets\wasm\uv_unwrap_simple.js 2>&1 |
    Where-Object { $_ -like '[[]wasm]*' -or $_ -like '*复现*' -or $_ -like '[[]OK]*' }
}
```

harness 参数：`--sanitized`（强制用清洗后网格）、`--no-repair`（完全不做清洗）、`--module <glue.js>`。

---

## 8. 遗留问题（未处理，供后续决定）

1. **其它 wasm 模块带同一隐患，需各自重建才生效**：`bd_lscm`（同页 BD-LSCM）、`uv_unwrap_field`、
   `uv_unwrap_abel_jacobi`、`bd_deformation`、`bdhm`、`ruppert`——有 make 的机器上 `make build-page-all`
   （或 `make build-all`）即可；独立构建脚本如 `cpp/Fluid3D/wasm/build.ps1` 也建议补同样两个参数。
2. **页面 JS 的一个清洗结果丢弃 bug**：`uv-unwrap-simple.html:1253-1259`

   ```js
   const repair = repairMeshForSolver(meshData);
   if (repair.edgeSplits > 0 || repair.vertexSplits > 0) {   // ← 只在发生分裂时才采用
     meshData = repair.meshData;
   ```

   `repairMeshForSolver` 开头会丢弃退化面（重复索引）与越界面，但若没发生边/点分裂，这份清洗结果被丢弃，
   原始面表照样进 wasm。`collectMeshData` 按 `Math.round(x*1e5)` 合并顶点，扫描类模型可能因此产生 `(i,i,k)`；
   本模型未踩到（合并 0 个顶点、非流形边 0），但建议改成无条件 `meshData = repair.meshData`。
3. `solve_lscm` 的签名把锚点写成 `int /*a1*/, int /*a2*/` 直接忽略，所以「改pin点」按钮对 LSCM 结果无效。
4. 可选优化（不再是修 bug 必需）：`solveLeastSquares` 由"正规方程 + 已 deprecated 的 `SimplicialCholesky`"
   改为 `Eigen::LeastSquaresConjugateGradient`，可去掉 `At`/`At*A`/多份拷贝与 Cholesky fill-in，
   同时避免条件数平方。

---

## 9. 目录说明（`.tmp_lscm_dbg/`）

| 文件 | 用途 |
| --- | --- |
| `bindings_lscm_dbg.cpp` | 只含 LSCM 路径的最小诊断 binding（`solve_lscm` 与正式版一致，额外导出 `dbg_*` 统计） |
| `run_lscm.js` | Node 复现/回归脚本，复刻页面 `normalizeObject` + `collectMeshData` 去重 + `repairMeshForSolver` 规则 |
| `uv_unwrap_simple_dbg.js/.wasm` | 带 `ASSERTIONS=2 / SAFE_HEAP=1 / STACK_OVERFLOW_CHECK=2` 的调试模块（定位栈溢出用） |
| `backup/uv_unwrap_simple.js/.wasm` | 修复前的正式产物备份（也可从 git 恢复） |

该目录为临时目录、未纳入 git；确认浏览器验证通过后可删除，或保留作回归工具（若保留建议加入 `.gitignore`）。

---

## 10. 关键代码位置索引

| 位置 | 内容 |
| --- | --- |
| `cpp/conformal-parameterization/wasm/Makefile:21-45` | 本次修改的构建参数 |
| `cpp/conformal-parameterization/Parameterization/SimpleParam/LSCM/Lscm.cpp:187-198` | `solveLeastSquares`（触发点：`SimplicialCholesky(At*A)`） |
| `cpp/deps/eigen-3.4.0/Eigen/src/SparseCholesky/SimplicialCholesky_impl.h:58,115-117` | 栈上临时数组（alloca） |
| `cpp/deps/eigen-3.4.0/Eigen/src/Core/util/Memory.h:592-598` | `ei_declare_aligned_stack_constructed_variable` |
| `cpp/deps/eigen-3.4.0/Eigen/src/Core/util/Macros.h:576-579` | `EIGEN_STACK_ALLOCATION_LIMIT 131072` |
| `cpp/conformal-parameterization/wasm/bindings_uv_unwrap_simple_compat.cpp:93-104` | `solve_lscm` 入口 |
| `uv-unwrap-simple.html:1252-1361` | 页面 LSCM 调用与错误映射 |
| `uv-unwrap-simple.html:881-1010` | `repairMeshForSolver`（第 8 节第 2 条） |
