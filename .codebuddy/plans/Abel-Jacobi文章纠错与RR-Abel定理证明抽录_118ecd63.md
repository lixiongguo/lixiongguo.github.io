---
name: Abel-Jacobi文章纠错与RR-Abel定理证明抽录
overview: 主文四处实质纠错（四次微分/除子 k−4/deg=8g−8/Abel 条件与 RR 分工）；新增同系列证明文章，以《黎曼曲面导引》为主干严格照录，补齐中间逻辑节点，并对每条定理给出「解析—几何」两条证明路线的并列对照。
todos:
  - id: fix-main-quartic
    content: 改写主文 L110–132：四次微分、$k-4$ 除子、$\deg D_Q=8g-8$、删去伪矛盾论证
    status: completed
  - id: fix-main-rr-abel
    content: 修正 L136–142 的 $L(D)/\ell(D)$ 与 $\ell(kK-D)$，改写 L240–245 的 Abel 定理并补逆定理
    status: completed
  - id: fix-main-role
    content: 改写 L108/L132 的 RR 定位句与 L288–290 结论段措辞，输出逐处 old→new 摘要
    status: completed
    dependencies:
      - fix-main-quartic
      - fix-main-rr-abel
  - id: source-align
    content: Use [skill:pdf] 核对缓存文本，定位定理 3.3.1/3.5.4/3.5.9/3.5.13 及其依赖，建立 OCR 讹字还原清单
    status: completed
  - id: write-rr-chapter
    content: 写 §0 路线总览与 §3 RR 章：照录＋编号节点＋【补】展开＋A1/A2 双路径对照表
    status: completed
    dependencies:
      - source-align
  - id: write-abel-chapters
    content: 写 §4 双线性关系、§5 Abel、§6 Jacobi、§7 Gu 对照章、附录 A 依赖图与 §8 主文对应
    status: completed
    dependencies:
      - source-align
  - id: verify-docs
    content: Use [mcp:packpdf] packpdf_check 校验公式与引用，复核术语一致性与两书符号隔离
    status: completed
    dependencies:
      - fix-main-role
      - write-rr-chapter
      - write-abel-chapters
---

## 用户需求

围绕 `_posts/1.Parameterization/3.微分几何方法的曲面展开/2019-06-01-Abel-Jacobi映射.md`（下称主文）做两件事，并按新要求提高可读性。

## 任务一：修订主文（仅纠错档）

依据 Quad I/II/III 原始论文与 Gu 讲义，改正 4 处实质错误，不动其余措辞：

1. 「四边形网格与亚纯二次微分的除子」整节重写：对象改为**亚纯四次微分** $(dz)^4$，除子系数由 $4-k$ 改为 $k-4$（3-价为一阶极点、5-价为一阶零点），度数由 $4g-4$ 改为 $8g-8$，删去「$4\chi=4-4g$ 与 $4g-4$ 相差符号」的伪矛盾论证（该式与 Poincaré–Hopf 是恒等式）。
2. Riemann-Roch 一节：给出 $L(D)$ 与 $\ell(D)$ 的精确定义，$k$-形式版本写成 $\ell(kK-D)$。
3. Abel 定理：补 $\deg D=0$ 前提，给出可用形式 $\mu(D_Q-4(\omega_0))=0$ 与逆定理构造 $\omega=f\omega_0^4$。
4. 「RR 给充分性」的定位改为「Abel 给存在性，RR 给解空间维数」；结论段「亚纯二次微分」改为「亚纯 $n$-形式（四边形四次、三角六次）」。

## 任务二：新增独立证明文章（本次重点）

新建同目录 `2019-06-02-Abel-Jacobi与Riemann-Roch定理证明.md`，把 Riemann-Roch、双线性关系、Abel 定理、Jacobi 反演的**陈述与证明**从文献中抽出，严格照录，并满足两条新要求：

- **中间逻辑节点**：每个证明按步骤切分编号节点，逐点说明「已知什么 / 依据哪条引理或公式 / 得到什么」；原文跳步处必须显式补出；每条引理标注它在后续哪一步被使用，避免引理悬空。
- **两种证明方式对照**：给出并列对照表（前提假设 / 核心工具 / 关键一步 / 难点 / 结论强度 / 可计算性），读者能在两条路线间来回比对；RR 一章额外给「同一本书内的两条路径」作二级对照。

## 阅读效果

主文成为一条自洽判据链：Poincaré–Hopf（计数恒等式）→ 四次微分除子 → Abel–Jacobi（位置可解性）→ 周期整化（无缝性），不再出现「二次微分 / 符号相反」这类中断推导的表述。新文章作为证明附件，可在定理编号（3.3.1 / 3.5.4 / 3.5.9 / 3.5.13）与主文段落之间互相跳转，且每一步都能看出依据。

## 技术栈与实施策略

纯 Markdown（Jekyll post + MathJax），不涉及构建改动。文献文本沿用已跑通的 `pypdf` 抽取缓存，成品用 `packpdf_check` 校验公式与引用规范。

## 主文四处修改（锚点已核对，最小 diff）

**(1) L110–132 整节替换**，正确链条：

- 四边形网格诱导的全局对象是**亚纯四次微分** $\omega=(dz_f)^4$（$K^4$ 的截面）；面/边/正则顶点间转移只差 $e^{\mathbf i n\pi/2}$，故 $(dz)^4$ 全局拼接；
- 奇异顶点 $z_v=w_v^{4/k}$，代入得 $(\tfrac k4)^4z_v^{k-4}(dz_v)^4=\omega$，即 $\operatorname{ord}_v(\omega)=k-4$：3-价简单极点、5-价简单零点；
- $D_Q=(\omega_Q)=\sum_v(k(v)-4)v$，$\deg D_Q=8g-8=4(2g-2)$；
- $\sum_v(k-4)n_k=2E-4V=-4\chi=8g-8$ 与之恒等，故度数平衡不构成约束，唯一实质约束是 Abel。

**(2) L136–142**：改为 $L(D)=\{f\in\mathcal M(S):(f)+D\ge0\}\cup\{0\}$、$\ell(D)=\dim L(D)$；$k$-形式讨论改为 $\ell(kK-D)$。

**(3) L240–245**：改为「$\deg D=0$ 时 $D$ 为主除子 $\iff\mu(D)\equiv0$」＋「四边形网格须先减典范部分：$\mu(D_Q-4(\omega_0))=0$」＋逆定理一句。

**(4) L108、L132、L288–290**：改写 RR 定位句与结论段措辞（「亚纯 $n$-形式（四边形四次、三角六次）」）。L249/L262 的 $(dz)^6$、$z_v=w_v^{6/k}$ 属正确用法，不动。

## 证明文章的写作规范

### 出处与忠实度

- 主干：梅加强《黎曼曲面导引》定理 3.3.1（RR，依赖引理 3.3.2–3.3.4）、3.5.4（双线性关系，前置命题 3.5.1–3.5.2）、3.5.9（Abel，依赖命题 3.5.1–3.5.8、引理 3.5.10–3.5.11）、3.5.13（Jacobi，依赖命题 3.5.5/3.5.7、引理 3.5.12）；
- 补充章：Gu《CCG Lecture 11》Period Matrix 定理、Abel–Jacobi 正合列与 $\mathrm{Pic}(C)\cong J(C)$、三型微分存在性定理（用 RR 证），照录并标 PAGE 号；
- 严格照录：公式、符号、定理编号与原文一致，仅做 LaTeX 排版；OCR 讹字须按映射表逐处还原（`lpDq`→$l(D)$、`ipDq`→$i(D)$、`dpDq`→$d(D)$、`‰`→$\neq$、`ď`→$\le$、`ě`→$\ge$、`“`→$=$、`´`→$-$、`P`→$\in$、`¨ ¨ ¨`→$\cdots$、`x3.3`→§3.3 等）；保留原书「因子/除子」「主要因子/主除子」并用的措辞。

### 中间逻辑节点（与照录隔离）

- 原文照录用普通段落，一字不改；新增推导统一用引用块 `> **【补】**` 包裹，读者可一眼区分「原书」与「补充」；
- 证明体按 `定理 3.3.1-①、-②、…` 编号，每节点三要素：**前提（已知）→ 依据（引理/公式编号）→ 结论（得到）**；
- 原文中的「由 Serre 对偶可知」「同理可得」「由双线性关系直接推出」等跳步，全部展开为显式节点，并注明跳步依据；
- 每条引理在陈述后加一行「用途：用于 3.3.1-④」式标注；
- 附录 A 给依赖图（mermaid），节点标注「本篇照录 / 仅引结论」。

### 两条路线的对照

- **§0 路线总览**：路线 A（梅加强，Hodge 定理 + Serre 对偶，复分析/上同调）与路线 B（Gu 讲义，周期矩阵 + Abel–Jacobi 正合列 + Jacobi 反演，几何/拓扑）各自的前提、工具与收敛点；点明二者**共用**周期矩阵与双线性关系，**分歧**在 RR 的证明方式；
- **每章末「路线对照」表**，固定六栏：前提假设 / 核心工具 / 关键一步 / 难点 / 结论强度 / 可计算性；
- **RR 章额外二级对照**：A1 = Hodge 直接法（梅加强 §3.3，照录）；A2 = 线丛 + Serre 对偶法（伍鸿熙 §11–12，**仅给章节索引与思路提纲，明确标注该 PDF 为无文字层扫描件、无法逐字照录**）；
- 每条定理给一句「两路线交汇点」，例如 RR 归到同一个上同调计算 $\ell(D)-\ell(K-D)$。

### 章节骨架

§0 两条路线总览 → §1 出处与照录原则 → §2 记号与约定 → §3 定理 3.3.1（RR，含引理与 A1/A2 对照）→ §4 定理 3.5.4（双线性关系）→ §5 定理 3.5.9（Abel）→ §6 定理 3.5.13（Jacobi）→ §7 附：Gu 讲义对照（标 PAGE）→ §8 与主文的对应关系 → 附录 A 依赖图 → 附录 B OCR 讹字还原表。

## 目录结构

```
_posts/1.Parameterization/3.微分几何方法的曲面展开/
├── 2019-06-01-Abel-Jacobi映射.md                      # [MODIFY] 四处纠错，最小 diff
├── 2019-06-02-Abel-Jacobi与Riemann-Roch定理证明.md    # [NEW] 证明抽录，含节点编号与双路线对照
└── 参考文献.md                                        # [UNCHANGED] 本次不动
```

新文章 front matter 与系列一致：`layout: post`、`category: Parameterization`、`categories: ["Parameterization", "Parameterization-QuadRemedhing"]` 中的 Quad 子类沿用主文写法、`title: "Abel-Jacobi 与 Riemann-Roch 的证明"`。

## 风险控制

- 不臆造页码：伍鸿熙为扫描件，只引章节号（第二章 §5–6、第三章 §11–12、第五章 §19）；
- 两书符号不混排：梅加强章用 $l(D),i(D),d(D),\Psi,\mathrm{Pic}^0$；Gu 章用 $\mathbf A,\mathbf B,\Pi,\mu,\mathrm{Pic}(C)$，两章之间只加「另见」过渡句；
- 文本缓存路径 `C:\Users\lixio\AppData\Local\Temp\aj_txt\`（`f5.txt `黎曼曲面导引、`f2.txt `Lecture 11、`q2.txt `Quad II、`f4.txt `伍鸿熙目录）；若失效用 `pypdf` 重抽，PowerShell here-string 落盘必须 `[IO.File]::WriteAllText($p,$code,(New-Object System.Text.UTF8Encoding($false)))`，否则 BOM 会触发 `SyntaxError`；
- 不改 `参考文献.md`，不新增「度量刻画」「工程实现」小节，不加 RoSy 谱系段落。

## Agent Extensions

### Skill

- **pdf**
- Purpose: 核对缓存的 `f5.txt`/`f2.txt` 是否完整覆盖定理 3.3.1、3.5.4、3.5.9、3.5.13 的陈述与证明；缓存失效时重新抽取并定位原文段落，保证「严格照录」有据可查。
- Expected outcome: 每一条待照录定理都能对应到可逐句校对的原文纯文本（含页码标记），并据此建立 OCR 讹字还原清单。

### MCP

- **packpdf**
- Purpose: 用 `packpdf_check` 校验主文与新文章的公式规范、本地图片引用与 Jekyll `post_url` 链接是否成立。
- Expected outcome: 两篇 md 零告警；新文章可被 PackPDF 正常收录，公式渲染与交叉引用均可解析。