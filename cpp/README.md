# 编译
# 若当前在仓库根目录：cd cpp/emsdk
# 若当前已在 cpp 目录：cd emsdk
.\emsdk install latest
.\emsdk activate latest
.\emsdk_env.ps1
cd ..
em++ lscm_solver.cpp -o ../assets/wasm/lscm_solver.js -O3 -std=c++17 "-ID:/third_party/eigen-3.4.0" --bind -s MODULARIZE=1 -s EXPORT_NAME="LCMSolver" -s ALLOW_MEMORY_GROWTH=1 -s TOTAL_MEMORY=256MB -s WASM=1




# LSCM Solver WASM 编译说明

本文档说明如何将 C++ LSCM 求解器编译为 WebAssembly 模块。

## 前置条件

### 1. 安装 Emscripten SDK

Emscripten 是一个 LLVM 到 WebAssembly 的编译器工具链。

**Windows 安装步骤：**

1. 下载并安装 Emscripten SDK（本仓库已包含 submodule）：
   ```powershell
   # 从仓库根目录
   cd cpp/emsdk
   # 若已在 cpp 目录，则用：cd emsdk

   .\emsdk install latest
   .\emsdk activate latest
   .\emsdk_env.ps1
   ```

   若 `install` 下载 wasm-binaries 时 SSL 中断，可手动用 curl 下载后重试：
   ```powershell
   curl.exe -L --retry 5 -o downloads/1724b50443d92e23ef2a56abf0dc501206839cef-wasm-binaries.zip `
     https://storage.googleapis.com/webassembly/emscripten-releases-builds/win/1724b50443d92e23ef2a56abf0dc501206839cef/wasm-binaries.zip
   .\emsdk install latest
   ```

2. 验证安装：
   ```powershell
   em++ --version
   ```

### 2. 下载 Eigen 库

Eigen 是一个高性能的 C++ 线性代数库。

1. 从官网下载：[https://eigen.tuxfamily.org/index.php?title=Main_Page](https://eigen.tuxfamily.org/index.php?title=Main_Page)
2. 解压到合适的位置，例如：
   - `E:\Dev\libs\eigen-3.4.0\` (Windows)
   - `~/libs/eigen/` (macOS/Linux)

## 编译步骤

### 方法一：使用 Makefile (推荐)

```powershell
# 检查环境配置
make check

# 编译
make
```

**重要：** 首次使用前，请编辑 `Makefile` 中的 `EIGEN_PATH` 变量，指向你的 Eigen 库路径。

### 方法二：手动编译

```powershell
em++ lscm_solver.cpp -o ../assets/wasm/lscm_solver.js ^
    -O3 -std=c++17 ^
    -IE:/Dev/libs/eigen-3.4.0 ^
    --bind ^
    -s MODULARIZE=1 ^
    -s EXPORT_NAME="LCMSolver" ^
    -s ALLOW_MEMORY_GROWTH=1 ^
    -s TOTAL_MEMORY=256MB ^
    -s WASM=1
```

### 编译选项说明

| 选项 | 说明 |
|------|------|
| `-O3` | 最高级别优化 |
| `-std=c++17` | 使用 C++17 标准 |
| `-I<path>` | Eigen 头文件路径 |
| `--bind` | 启用 Embind (JS/C++ 互操作) |
| `-s MODULARIZE=1` | 导出 ES6 模块 |
| `-s EXPORT_NAME="LCMSolver"` | 模块变量名 |
| `-s ALLOW_MEMORY_GROWTH=1` | 允许动态内存增长 |
| `-s TOTAL_MEMORY=256MB` | WASM 内存大小 |
| `-s WASM=1` | 输出 WebAssembly |

## 输出文件

编译成功后，会生成两个文件：

1. `assets/wasm/lscm_solver.js` - JavaScript 胶水代码
2. `assets/wasm/lscm_solver.wasm` - WebAssembly 二进制文件

这两个文件都需要部署到 GitHub Pages。

## 验证部署

部署后，打开 `uv-unwrap.html`，控制台应该显示：

```
WASM LSCM 求解器加载成功 (Eigen 稀疏 Cholesky)
```

如果显示 WASM 加载失败，请检查：

1. 文件是否正确上传到 `assets/wasm/` 目录
2. GitHub Pages 是否正确配置
3. 浏览器控制台是否有跨域错误

## 性能对比

| 指标 | 旧版 (JS 稠密) | 新版 (WASM + Eigen) |
|------|---------------|---------------------|
| 算法 | 高斯消元 O(n³) | 稀疏 Cholesky ~O(n^1.5) |
| 内存 | O(n²) 稠密 | O(n) 稀疏 |
| 大模型 (10万+ 顶点) | 可能卡顿 | 流畅 |
| 数值稳定性 | 一般 | 更优 (Eigen 成熟实现) |

## 常见问题

### Q: 编译报错 "Eigen/Dense not found"

A: 检查 `-I` 参数路径是否正确，确保指向包含 `Eigen` 目录的父文件夹。

### Q: 运行时 WASM 加载失败

A: 可能是 WASM 文件未被 Jekyll 复制到输出目录。检查 `_config.yml` 中的 `keep_files` 配置。

### Q: 大网格下报 `memory access out of bounds`（页面提示"WASM 内存越界"，曾误称"内存不足"）

A: 这**不是**堆内存不足，而是 Eigen 稀疏 Cholesky/LLT/LDLT 的工作区（`Index tags[size]`、`pattern[size]`、`Scalar y[size]`）被 `alloca` 到 wasm 栈上导致的**栈溢出**：
Eigen 的阈值 `EIGEN_STACK_ALLOCATION_LIMIT` 默认 128KB（按桌面栈设计），而 Emscripten 默认栈只有 64KB，
`v = 2(V-2) > 16384`（约 8.2K 顶点以上）就会踩到。增大 `-s TOTAL_MEMORY` 对此**无效**。

修法：
- `-DEIGEN_STACK_ALLOCATION_LIMIT=0`（阈值置 0 ⇒ 这些缓冲区一律走 `aligned_malloc`，必须）
- `-s STACK_SIZE=1048576`（兜底，建议）
- 定位手段：`-sASSERTIONS=2 -sSAFE_HEAP=1 -sSTACK_OVERFLOW_CHECK=2 -g` 重建，会直接打印 `stack overflow (Attempt to set SP to ...)` 与调用链

详见「参数化算法 — 代码实现汇总」的 WebAssembly 编译章节。
（只有真的堆耗尽、报 `Aborted(OOM)` / `Cannot enlarge memory arrays` 时，才轮到内存相关参数。）
