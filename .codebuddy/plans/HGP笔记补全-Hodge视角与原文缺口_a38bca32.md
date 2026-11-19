---
name: HGP笔记补全-Hodge视角与原文缺口
overview: 把 HGP 笔记按「正文级缺口补进原笔记 + 技术细节另立注记」的方式补全：原笔记补离散 1-形式/调和性定义、权重取法、frame 软化策略与定理假设的精确表述并修正公式编号；新建《HGP 注记：Hodge 视角与原文对照》承载离散 Hodge 定位说明、逐节对照表、指标理论细节与附录 A/B 技术点。不写实验结果与局限。
todos:
  - id: extract-paper
    content: Use [skill:pdf] 抽取原文 §3–§7 与附录，取出式 (6)(7)(14)、Lemma 5.4 与 mean value coordinates 原句
    status: completed
  - id: add-preliminaries
    content: 在 HGP.md 插入「预备：离散 1-形式、余闭与指标」与「全局参数化」定义节，含记号表
    status: completed
    dependencies:
      - extract-paper
  - id: fix-numbering
    content: 把 HGP.md 的 RHS/LHS 由 (6)(7) 改为 (9)(10)，逐处标注原文编号
    status: completed
    dependencies:
      - add-preliminaries
  - id: patch-system-algo
    content: 补 mean value 权重、式 (14)、§7 软化策略与 frame 同源、Theorem 6.1 精确假设
    status: completed
    dependencies:
      - fix-numbering
  - id: write-notes
    content: 新建《HGP 注记：Hodge 视角与原文对照》，写离散 Hodge 定位、逐条对照、指标细节与附录 A/B
    status: completed
    dependencies:
      - extract-paper
  - id: verify-docs
    content: Use [mcp:packpdf] 校验两篇公式与 post_url，复核编号、术语与互链一致
    status: completed
    dependencies:
      - patch-system-algo
      - write-notes
---

## 用户需求

围绕 `_posts/1.Parameterization/2.几何优化方法/2018-03-15-全局调和参数化-HGP.md` 与原文 `_posts/PDFs/Harmonic_Global_Parametrization.pdf`（Bright–Chien–Weber, *Harmonic Global Parametrization with Rational Holonomy*, TOG 36(4) 2017），回答「原文用了 Hodge 定理，为什么笔记里没有」，并系统排查笔记相对原文的缺口后补齐。

## 核实结论（写入两篇文档的前提）

原文全文检索「Hodge」出现 0 次；论文的调和概念是离散的：§3.2.2 定义「闭 + 余闭 = 调和」，并明言只用 **mostly harmonic** 1-形式；Hodge 定理只在 §2.1 相关工作中以「Gu–Yau 的 holomorphic 1-forms 是正交调和 1-形式对」的形式间接出现。因此正确表述是：论文未调用 Hodge 定理，Hodge 只作背景；笔记真正缺的是「离散 1-形式 / 余闭 / 调和」这一层定义，而不是一条定理。

## 待补缺口（已与原文逐节比对）

- §3.2.1–3.2.4：离散 1-形式定义、闭/余闭、指标定义与指标公式、wheel 定义与引理，全部缺失。
- §3.3：全局参数化、cone metric、seamless 的正式定义缺失（现只有 seam graph、holonomy 两句）。
- §4：权重取 mean value coordinates 未写；一般度数 seam 顶点条件 (14) 一笔带过。
- §5.2.1 / Lemma 5.4：边界分量与边界指标贡献缺陈述。
- §6：Theorem 6.1 的假设（锥三角形与边界三角形正向定向、诱导度量实现目标锥角与边界转角）未精确化。
- §7：缺「软化调和约束」策略、frame 与 holonomy 同源（Bommes 2009 frame field）、高亏格可行性问题、7.1 Frame Fixing。
- 公式编号错位：笔记把 RHS/LHS 记作 (6)(7)，原文实为 (9)(10)；原文 (6)(7) 是旋转约束与调和条件。
- 附录 A（式 (14) 推导）、附录 B（vanishing 1-forms）缺失；记号 $k_i,l_j,e_P,N,\phi,s,\mathrm{scg}_\rho$ 无对照表。

## 交付方式（用户已选定）

1. **拆两篇**：`HGP.md` 只补正文级缺口（§3 离散定义、§4 权重、§7 软化与 frame、定理假设）；新建《HGP 注记：Hodge 视角与原文对照》承载 Hodge 定位说明、逐条原文对照表、指标细节、附录 A/B。
2. **Hodge 深度**：只写离散版 + 定位说明，不写连续 Hodge 定理及其证明。
3. **不补** §8 实验结果与 §9 局限，笔记保持「方法笔记」定位；不删既有内容与图片。

## 阅读效果

打开 `HGP.md` 即能从「离散 1-形式 → 闭/余闭/调和 → 指标与 wheel → q-CCM → 分支覆盖 → 指标预算 → 算法」一路读通，公式编号与原文一致；想知道 Hodge 到底在哪儿、原文哪节漏了、附录怎么推，转到注记文即可逐条对照。

## 技术栈与实施策略

纯 Markdown（Jekyll post + MathJax，`mathjax: true`），无构建改动。原文公式一律从 PDF 现抽现抄，不凭记忆默写；两篇成文后用 `packpdf_check` 校验公式规范与 `post_url`。

## 一、原文抽取（写公式前必做）

- 用 `[skill:pdf]` 抽取 `Harmonic_Global_Parametrization.pdf`（15 页）。必须目标页：p4–p6（§3.2.1–§3.3）、p7–p8（§4 式 (6)(7)、§5 开头）、p9–p10（Lemma 5.2/5.3/5.4、式 (9)(10)、Theorem 6.1、§7）、p10–p11（§7.1 Frame Fixing、mean value coordinates 原句）、p14（附录 A 式 (14) 推导、附录 B）。
- Windows 控制台为 GBK，pypdf 输出须先 `sys.stdout.reconfigure(encoding='utf-8',errors='replace')`。
- 连字还原表（引用原文时必须替换）：`/f_i`→`fi`、`de/f_inition`→`definition`、`/v.alti`→$\hat v_i$、`/afii10069.ital`→$g$、`convexi/f_ication`→`convexification`。
- 抽取结果只在会话内对照使用，不落盘缓存。

## 二、`HGP.md` 的改造（最小 diff，只加不删）

### 插入点（按行号，行号以当前 338 行为准）

| 位置 | 动作 |
| --- | --- |
| L12 `## 对CCM进行推广-q-CCM定义` 之前 | 插入新节 `## 预备：离散 1-形式、余闭与指标` |
| L30–L36 的 (1) 之后 | 补一句「$w_{ij}$ 取 mean value coordinates（原文 §4）」 |
| L153–L155 `## 理论保证` 开头、Theorem 6.1 之前 | 补「正向定向」「诱导度量实现目标角」的精确定义 |
| L196–L211 的 `\tag{6}` | 改为 `\tag{9}`，并在公式后注明「原文 (9)」 |
| L245–L250 的 `\tag{7}` | 改为 `\tag{10}`，注明「原文 (10)」 |
| L255 「对比 (6)(7)」 | 改为「对比 (9)(10)」 |
| L287 `##  HGP 算法实现` 内 | 补「软化策略」「frame 与 holonomy 同源」「高亏格可行性」三段 |
| L303–L308 的 (8) | 保留编号，公式后注明「原文 (14)；度数 2 的特例」 |
| 文末 | 加一行指向注记文的链接 |


### 新节 `## 预备：离散 1-形式、余闭与指标` 的内容

1. **记号表**（12 行）：$S$、$S_c$、$\tilde S_q$、$G_s$、$\rho$、$\mathrm{scg}_\rho$、$k_i$（锥指数，锥角 $2\pi k_i/q$）、$l_j$（边界转角指数）、$e_P$（分歧指数）、$N=k_i/\gcd(k_i,q)$、$\phi$（边界分量转角倍数）、$s$（内部指标贡献）。
2. **离散 1-形式**（原文 Definition 3.2）：每条半边赋一个实数，反向取负 $\rho_{ji}=-\rho_{ij}$。
3. **闭**：绕一个面一圈求和为零 $\sum_{\partial t}\rho_{ij}=0$；**余闭**：顶点处按权重求和为零（等价于 $L_1\rho=0$，$L_1$ 为 1-形式 Laplacian）；**调和 = 闭 + 余闭**。
4. **mostly harmonic 的原文定位**：正文引原话「We do not utilize fully harmonic 1-forms, but 1-forms that are mostly harmonic」，并说明 HGP 只要求内部非锥、非边界处调和。
5. **指标**（Definition 3.3）：$\mathrm{ind}*\rho(p)=\frac{1}{2}\left(2-\mathrm{scg}_\rho(p)\right)$；**指标公式**（Theorem 3.4，原文式 (5)）：$\sum*{v\in V}\mathrm{ind}(v)+\sum_{f\in F}\mathrm{ind}(f)=\chi(S)=2-2g$；**Lemma 3.5**：非零 1-形式在闭或余闭处指标 $\le 0$。
6. **wheel**（Definition 3.6）：1-ring 上相邻半边的带符号角 $\gamma_i$ 同号且 $\sum_i|\gamma_i|=2\pi$；**Lemma 3.7**：非 wheel 顶点必存在某 $\rho^{\alpha,\beta}$ 使其指标严格为负。
7. **全局参数化**（§3.3）：seam graph $G_s$ 切开得 $S_c$；若缝两侧像等长则拉回平面度量得 cone metric $\mu_f$；seamless 定义为缝两侧像差一个保持定向的等距（旋转部分为 $\pi/2$ 的整数倍，本文推广为 $2\pi/q$ 的整数倍）。

### 算法节新增三段

- **frame 与 holonomy 同源**：结果中的 frames 与目标 holonomy 都由 [Bommes et al. 2009] 的 frame field 决定；低亏格稳定，高亏格需软化。
- **软化策略**：旋转约束 (6) 保持为硬约束，调和约束 (7)(14) 软化进目标函数，避免 frame 与 q-CCM 线性空间冲突导致不可行；SOCP 每模型 1–2 次迭代即可（不写具体实验数字，只写机制）。
- **frame fixing（§7.1）**：每步按 frame 条件更新 $d$，初值 $d=(1,0)$；若 frame 与旋转约束不相容则回退。

### Theorem 6.1 的精确假设

补三条：锥点处的三角形像正向定向（行列式为正）；边界三角形同；诱导度量在锥点实现目标锥角 $2\pi k_i/q$、在边界实现目标转角 $2\pi l_j/q$。并注明这三条正是 $F_{cb}$ 只取锥/边界邻域三角形的原因。

## 三、新文件

`_posts/1.Parameterization/2.几何优化方法/2018-03-16-HGP注记-Hodge视角与原文对照.md`

front matter 与同目录一致：`layout: post`、`title: "HGP 注记：Hodge 视角与原文对照"`、`categories: ["Parameterization", "Parameterization-GeometricOptimization"]`、`mathjax: true`。

章节骨架：

- §0 分工表（主笔记 / 本注记 / 原文小节三方对应）
- §1 **Hodge 视角（离散版）**
- 连续背景一句话：Hodge 分解把闭形式拆成调和 + 恰当 + 余恰当，调和即闭且余闭；Gu–Yau 的全纯 1-形式就是一对正交调和 1-形式（原文 §2.1 原话）。
- 离散对应：$L_1$、$\delta\rho=0\iff L_1\rho=0$、闭 + 余闭 = 离散调和；权重 $w_{ij}$ 取 mean value 而非 cotan 时，余闭条件随之改变，但不影响指标论证（指标只用到「加权和为零」这一条）。
- **定位**：原文 0 次「Hodge」；HGP 只需 mostly harmonic，因为 Lemma 3.5 是逐点性质，不需要全局 Hodge 分解；Hodge 只解释「为什么调和是自然的」与「为什么全纯 1-形式路线畸变高」。
- §2 逐条原文对照表（列：原文小节 / 内容 / 主笔记位置 / 状态）
- §3 指标计数细节：§3.2.5 圆盘情形（内部 $s$、边界 + 外侧面合计 2）、§3.2.6 非凸推广
- §4 Lemma 5.4 的陈述与「每个边界分量贡献 $1+l_j/\gcd(l_j,q)$」的来历；§5.2.1 边界分量个数
- §5 附录 A：式 (14) 推导（$r_0=0$、$r_s=\sum_{j=1}^{s}\theta_j$、$N^*(\hat v_i^s)$ 的取法、循环求和式）
- §6 附录 B：vanishing 1-forms（非零假设为何需要单独处理、Gortler et al. 2006 §4.15 的路线）
- §7 公式编号对照表（本文 vs 原文）+ 连字还原表

## 四、编号与交叉引用规则

- 全篇以原文编号为准：(4) Riemann–Hurwitz、(5) Gauss–Bonnet + 指标公式、(6) 旋转约束、(7) 非 seam 调和、(9) RHS、(10) LHS、(14) 一般度数 seam 顶点。
- 主笔记中沿用自编号的 (1)(2)(3)(8) 保留，但每处加「原文 (n)」标注；冲突项 (6)(7) 必须改成 (9)(10)，否则与原文 (6)(7) 语义碰撞。
- 两篇互链用 `{% post_url 1.Parameterization/2.几何优化方法/2018-03-15-全局调和参数化-HGP %}` 与反向链接；不改 `参考文献.md`，不动既有图片绝对路径。

## 五、质量与校验

- 公式规范： `前后留空格、范数写 `\lVert \rVert`、表格单元格内不出现裸 `|`、`\tag` 编号连续。
- 事实校验点：Theorem 3.4 与 Lemma 3.5 的编号、$\gcd$ 相关三条引理、式 (14) 的权重与旋转因子、mean value coordinates 的原句归属页。
- 术语统一：cone metric、seamless、holonomy、wheel、ramification point、mostly harmonic 全文一致，不出现「调和映射 / 调和 1-形式」混用。

## Agent Extensions

### Skill

- **pdf**
- Purpose: 抽取 `Harmonic_Global_Parametrization.pdf` 的 §3.2–§3.3、§4、§5.2、§6、§7.1 与附录 A/B 原文，取回式 (6)(7)(14)、Lemma 5.4、mean value coordinates 原句等需逐字引用的内容。
- Expected outcome: 得到可与笔记逐句核对的纯文本（含页码标记与连字还原），据此写下两篇文档中的公式与引语。

### MCP

- **packpdf**
- Purpose: 用 `packpdf_check` 校验两篇 Markdown 的公式规范、图片引用与 `post_url` 链接。
- Expected outcome: 两篇零公式告警、`post_url 引用：断裂 0 处`，新注记文可被 PackPDF 正常收录。