# SuperSplat

> PlayCanvas 出品的 **3D Gaussian Splat** 编辑 / 发布平台。  
> Editor 在线：[superspl.at/editor](https://superspl.at/editor) · 平台：[superspl.at](https://superspl.at)  
> 开源：[`playcanvas/supersplat`](https://github.com/playcanvas/supersplat)（MIT）· Viewer：[`supersplat-viewer`](https://github.com/playcanvas/supersplat-viewer) · 转换 CLI：[`splat-transform`](https://github.com/playcanvas/splat-transform)  
> 文档：[PlayCanvas User Manual — SuperSplat](https://developer.playcanvas.com/user-manual/gaussian-splatting/editing/supersplat/)

训练出 [3DGS](3DGS.md) 之后，原始 PLY 常带浮点（floaters）、背景杂点、尺度不齐。SuperSplat 解决的是 **后处理与交付**：浏览器里清理、变换、调色、合并，再导出或一键发布到可分享 / 可嵌入的 Web Viewer。编辑在本地浏览器完成，**未主动 Publish 前数据不上传**。

## 1. 平台组成

| 部件 | 作用 | 入口 |
|:---|:---|:---|
| **Editor** | 清理、裁剪、调色、动画相机；开源 | [superspl.at/editor](https://superspl.at/editor) |
| **Direct Upload** | 已干净的 splat，跳过编辑直接发布 | 首页橙色 Upload |
| **Manage** | 库管理：标题、可见性、许可、进 Studio | [superspl.at/manage](https://superspl.at/manage) |
| **Studio** | 观看体验编排：相机、动画、标注、后效、天空盒、碰撞 | `scene/<hash>/studio` |
| **Scene / Explore** | 公开页与画廊 | [superspl.at](https://superspl.at) |
| **Viewer** | 开源 Web 查看器（npm / 自托管） | `@playcanvas/supersplat-viewer` |
| **Convert** | 浏览器前端调 `splat-transform`：格式转换 / 变换 / 过滤 | [superspl.at/convert](https://superspl.at/convert) |

开源与托管分层：Editor / Viewer / splat-transform 为 MIT；Studio、Manage、Explore、发布 API 由 PlayCanvas 托管在 `superspl.at`。发布、点赞、评论需账号；浏览公开页可匿名。

## 2. 在管线中的位置

```text
多视角图像
  → SfM（常 COLMAP）得位姿
  → 3DGS / 变体训练  →  *.ply（高斯属性）
  → SuperSplat Editor（清理 / 对齐 / 调色 / 合并）
  → 导出 PLY / Compressed PLY / SOG
     或 Publish → Studio 编排 → Scene 链接 / Embed
```

相对 [NeRF](../3.NeRF/Nerf.md) 系：3DGS 本就是显式高斯点集，天然适合「选中—删除—变换」式编辑；SuperSplat 把这套做成生产向 Web 工具，而不是再训一场网络。

## 3. 环境与输入

- 浏览器：Chrome / Firefox / Safari / Edge；**WebGL 2.0** 即可编辑。
- **WebGPU**：导出 **SOG**、独立 Viewer 包等能力需要；无 WebGPU 时仍可编、可导出普通 / 压缩 PLY。
- 大场景依赖 GPU 显存与浏览器内存；可用 Solo 只显一轨、导入时降 LOD、先删杂点再细修。

输入必须是 **3DGS 语义的 PLY**（含 `x,y,z`、`scale_*`、`rot_*`、opacity、`f_dc_*` 等），普通三角网格 / 裸点云 PLY 会加载失败。可拖多份进 Scene Manager 做合并。

工程可存 `.ssproj` 保留编辑状态；最终交付再 Export。

## 4. Editor 核心能力

### 4.1 选择与清理

| 工具 / 操作 | 用途 |
|:---|:---|
| Rect / Brush / Lasso / Sphere / Box / Flood 等 | 框选、刷选、体选、洪水选孤立块 |
| **Rings** vs **Centers** | Rings：只打到最前可见层；Centers：穿透选中心 |
| Delete / Undo / Reset | 删点可撤销；Reset 恢复本轨已删高斯 |
| Lock（`H`）/ Unlock | 锁住已修好区域，避免误删 |
| Invert + Delete | 保留选中区域、裁掉其余（crop） |
| Separate | 选中抽成新一层 |
| Splat Data 面板 | 按透明度、尺度等属性范围批量选 |

常见配方：Rings + Flood/Lasso 清浮点 → Invert 裁景 → Lock 保护区再扫周边 → 多视角检查 Undo。

### 4.2 变换、对齐、外观

- 对整轨 splat：平移 / 旋转 / 缩放；度量与对齐，方便多捕获拼进同一世界坐标。
- 颜色与外观：整体或属性级调整（色、不透明度、尺度等），做展示向润色。
- 多 splat：Scene Manager 显隐、Solo；合并后 **Export PLY** 得到单文件（注意 `.ssproj` Save ≠ 合并 PLY）。

### 4.3 导出格式

| 格式 | 说明 |
|:---|:---|
| **PLY** | 标准 3DGS PLY，互通性最好 |
| **Compressed PLY** | 量化压缩，体积远小于未压缩；常丢高阶 SH（见 PlayCanvas 压缩博文） |
| **SOG** | PlayCanvas 侧压缩格式；平台发布会压成 SOG；超约 100 万高斯可走 **Streamed SOG** 流式加载 |

本地自托管可用 Viewer + 导出文件，不必绑死托管站。

## 5. 发布与观看

1. Editor 内 Publish，或 Direct Upload。
2. Manage 里管理元数据与可见性。
3. Studio 加相机路径、标注、后效等。
4. 分享 Scene URL，或把 Viewer embed 到自己的站点。

观看侧常见 orbit / fly / walk；桌面与移动端浏览器均可。

## 6. 与相邻工具对照

| | SuperSplat | 训练侧 3DGS | 传统 MVS 网格编辑 |
|:---|:---|:---|:---|
| 对象 | 已训好的高斯 PLY | 从图像优化高斯 | 三角网格 / 点云 |
| 强项 | 清理、交付、Web 分享 | 新视角质量、细节 | CAD / 测量 / 物理碰撞成熟 |
| 弱项 | 不替代训练与位姿；大场景吃显存 | 原始结果常脏、难直接上线 | 弱纹理、高光难；编辑≠实时光场 |

适合：**扫完 / 训完 → 清脏 → 给客户链接或嵌入站内**。需要精确 mesh、UV、物理时，仍应走 NeuS / 网格重建或另抽表面，而不是只靠 splat 编辑器。

## 7. 一句话

**SuperSplat = 浏览器里的 3DGS 后期与发布台：开源 Editor 清浮点、裁景、对齐调色，导出 PLY/压缩/SOG，或发布到 superspl.at 用 Studio + Viewer 交付。**
