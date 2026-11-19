---
name: Abel-Jacobi文章纠错与RR-Abel定理证明抽录
overview: 对《Abel-Jacobi映射》文中三处符号/指数错误与 RR/Abel 角色定位做最小纠错；另按"严格照录"标准，以《黎曼曲面导引》(梅加强) 为主干、Gu CCG Lecture 11 为补充，把 Riemann-Roch、双线性关系、Abel 定理、Jacobi 反演的陈述与证明抽录为同系列独立文章。
todos:
  - id: fix-main-quartic
    content: 改写主文 L110–132 为「四边形网格与亚纯四次微分」：$k-4$、$\deg D_Q=8g-8$、删去伪矛盾论证
    status: pending
  - id: fix-main-rr-abel
    content: 修正主文 L136–142 的 $L(D)/\ell(D)$ 与 $\ell(kK-D)$，改写 L240–245 的 Abel 定理并补逆定理
    status: pending
  - id: fix-main-role
    content: 改写 L108/L132 的 RR 定位句与 L288–290 结论段措辞，输出逐处 old→new 摘要
    status: pending
    dependencies:
      - fix-main-quartic
      - fix-main-rr-abel
  - id: extract-rr-proof
    content: 用 [skill:pdf] 核对并从《黎曼曲面导引》照录定理 3.3.1 及引理 3.3.2–3.3.4 的陈述与证明
    status: pending
  - id: extract-abel-proof
    content: 照录定理 3.5.4（双线性关系）、3.5.9（Abel，含引理 3.5.10–3.5.12）、3.5.13（Jacobi）及所需前置命题
    status: pending
  - id: compose-article
    content: 新建 2019-06-02 文章：front matter、八节骨架、Gu 讲义对照章（标 PAGE 号）、与主文互相链接
    status: pending
    dependencies:
      - extract-rr-proof
      - extract-abel-proof
  - id: verify
    content: 用 [mcp:packpdf] packpdf_check 校验公式与引用，并复核术语一致性（二次 vs 四次、Abel vs RR 分工）
    status: pending
    dependencies:
      - compose-article
      - fix-main-role
---

## 用户需求

两条并行任务，都围绕 `_posts/1.Parameterization/3.微分几何方法的曲面展开/2019-06-01-Abel-Jacobi映射.md`（下称主文）展开。

## 一、修订主文（仅纠错档）

依据 Quad I/II/III 原始论文（Chen et al. CMAME 356 (2019)；Lei et al. CMAME 366 (2020)；Zheng et al.）与 Gu 的 CCG 讲义，改正主文 4 处实质错误，不动其余措辞与排版：

1. 「四边形网格与亚纯二次微分的除子」整节重写：对象由「亚纯二次微分」改为「亚纯四次微分」，除子系数由 $4-k$ 改为 $k-4$（3-价为一阶极点、5-价为一阶零点），度数由 $4g-4$ 改为 $8g-8$，并删去「$4\chi=4-4g$ 与 $4g-4$ 相差符号」的伪矛盾论证——该式与 Poincaré–Hopf 是恒等式。
2. Riemann-Roch 一节：给出 $L(D)$ 与 $\ell(D)$ 的精确定义，$k$-形式版本写成 $\ell(kK-D)$。
3. Abel 定理：补 $\deg D=0$ 前提；给出可用形式（Abel–Jacobi 条件 $\mu(D_Q-4(\omega_0))=0$）与逆定理（存在性构造 $\omega=f\omega_0^4$）。
4. 「Riemann-Roch 给出充分性」的定位改为「Abel 定理给存在性，Riemann-Roch 给解空间维数」；结论段「亚纯二次微分」改为「亚纯 $n$-形式（四边形四次、三角六次）」。

## 二、新增独立证明文章

新建同目录、同系列的 `2019-06-02-Abel-Jacobi与Riemann-Roch定理证明.md`，把 Abel–Jacobi 定理与 Riemann–Roch 定理的**陈述与完整证明**从文献中抽出，**两书对照合编**：以梅加强《黎曼曲面导引》为主干（完整证明、原书编号），Gu《CCG Lecture 11》作几何直观与补充（单独成节、标注 PAGE 号）。忠实度按「严格照录」：公式、符号、定理编号与原文一致，仅做 LaTeX 排版转换，不改写、不压缩为要点。

## 视觉与阅读效果

主文读起来是一条自洽的判据链：Poincaré–Hopf（计数恒等式）→ 四次微分的除子 → Abel–Jacobi（位置可解性）→ 周期整化（无缝性）；不再出现「二次微分 / 符号相反 / 相差符号」这类会中断推导的表述。新文章则可作为主文的证明附件，读者能在编号（定理 3.3.1、3.5.4、3.5.9、3.5.13）与主文段落之间来回跳。

## 技术栈与实施策略

纯 Markdown（Jekyll post + MathJax / LaTeX 公式），不涉及构建改动。文献抽取沿用已跑通的 `pypdf` 管线，成品用 `packpdf_check` 校验公式规范与引用。

已有缓存（无需重新抽取，直接 `read_file`）：
`C:\Users\lixio\AppData\Local\Temp\aj_txt\` 下 `f5.txt`（梅加强《黎曼曲面导引》，有文字层）、`f2.txt`（Gu Lecture 11）、`q2.txt`（Quad II）、`f4.txt`（伍鸿熙，仅目录）、`rosy.txt` 等。若缓存丢失，用 `pypdf` 重抽；PowerShell here-string 落盘必须 `[IO.File]::WriteAllText($p,$code,(New-Object System.Text.UTF8Encoding($false)))`，否则 `python -` 因 BOM 报 `SyntaxError: invalid non-printable character`。

## 主文四处修改（锚点已核对）

(1) L110–132 整节替换。正确链条：

- 四边形网格诱导的全局对象是**亚纯四次微分** $\omega=(dz_f)^4$（$K^4$ 的截面）；面/边/正则顶点间转移只差 $e^{\mathbf i n\pi/2}$，故 $(dz)^4$ 全局拼接；
- 奇异顶点 $z_v=w_v^{4/k}$，代入得 $(\tfrac{k}{4})^4z_v^{k-4}(dz_v)^4=\omega$，即 $\operatorname{ord}_v(\omega)=k-4$：3-价为简单极点、5-价为简单零点；
- $D_Q=(\omega_Q)=\sum_v(k(v)-4)v$，$\deg D_Q=8g-8=4(2g-2)$；
- $\sum_v(k-4)n_k=2E-4V=-4\chi=8g-8$ 与之恒等，故度数平衡不构成约束，唯一实质约束是 Abel。

(2) L136–142：改为 $L(D)=\{f\in\mathcal M(S):(f)+D\ge0\}\cup\{0\}$、$\ell(D)=\dim L(D)$；$k$-形式讨论改为 $\ell(kK-D)$。

(3) L240–245：改为「$\deg D=0$ 时 $D$ 为主除子 $\iff\mu(D)\equiv0$」＋「四边形网格须先减典范部分：$\mu(D_Q-4(\omega_0))=0$」＋逆定理一句（$\exists f,(f)=D_Q-4(\omega_0)$，取 $\omega=f\omega_0^4$）。

(4) L108 与 L132 的 RR 定位句改写；L288–290「亚纯二次微分」改为「亚纯 $n$-形式（四边形为四次微分，三角为六次微分）」。L249/L262 的 $\omega=(dz)^6$ 与 $z_v=w_v^{6/k}$ 属正确用法，不动。

## 证明抽录的取证要点（严格照录的前提）

梅加强《黎曼曲面导引》原书编号与依赖（已核）：

- 定理 3.3.1（RR）证明跨原文 p.66–71，依赖引理 3.3.2、3.3.3、3.3.4，以及 Hodge 定理／Serre 对偶的结论——后者须照录其陈述，避免「证明中空降结论」；
- 定理 3.5.4（双线性关系）→ 命题 3.5.1、3.5.2 为前置；
- 定理 3.5.9（Abel）→ 依赖命题 3.5.1–3.5.8、引理 3.5.10、3.5.11；
- 定理 3.5.13（Jacobi）→ 依赖命题 3.5.5、3.5.7（周期矩阵实部正定）、引理 3.5.12。

Gu Lecture 11 补充（标注原 PDF 页码）：

- Period Matrix 定理（$\mathbf A\mathbf B^{\mathsf T}=\mathbf B\mathbf A^{\mathsf T}$；$\sqrt{-1}(\mathbf A\bar{\mathbf B}^{\mathsf T}-\mathbf B\bar{\mathbf A}^{\mathsf T})$ Hermite 正定）；
- Abel–Jacobi 正合列与 $\mathrm{Pic}(C)\cong J(C)$；
- 三型 Abelian 微分存在性定理（以 RR 证明）。

**OCR 讹字映射表（照录时必须逐处还原，否则会抄错数学）**：`lpDq`→$l(D)$、`ipDq`→$i(D)$、`dpDq`→$d(D)$、`‰`→$\neq$、`ď`→$\leq$、`ě`→$\geq$、`“`→$=$、`´`→$-$、`P`→$\in$、`t u`→$\{\}$、`p1q`→$(1)$、`¨ ¨ ¨`→$\cdots$、`ϕ`→$\phi$、`x3.3`→§3.3、`RpDq`→$R(D)$。照录时保留原书「因子」与「除子」并用、「主要因子」与「主除子」并用的措辞，不统一改写。

## 硬约束与风险控制

- 不臆造页码：伍鸿熙《紧黎曼曲面引论》为无文字层扫描件，只能引章节号（第二章 §5 因子、§6 RR；第三章 §11 Hodge 与 Serre 对偶、§12 RR 证明；第五章 §19 陈类与 Gauss–Bonnet）；
- 两书符号不混排：梅加强章节沿用 $l(D),i(D),d(D),\Psi,\mathrm{Pic}^0$；Gu 章节沿用 $\mathbf A,\mathbf B,\Pi,\mu,\mathrm{Pic}(C)$，中间只加「另见」过渡；
- 主文改动以最小 diff 为限，改完列出逐处 old→new 摘要供复核；
- 不改同目录 `参考文献.md`，不新增「度量刻画」「工程实现」小节，不加 RoSy 谱系段落。

## 文件结构

```
_posts/1.Parameterization/3.微分几何方法的曲面展开/
├── 2019-06-01-Abel-Jacobi映射.md                      # [MODIFY] 四处纠错
└── 2019-06-02-Abel-Jacobi与Riemann-Roch定理证明.md    # [NEW] 独立证明文章
```

新文章 front matter 与系列一致（`layout: post`、`category: Parameterization`、`categories: ["Parameterization", "Parameterization-QuadRemeshing"]`、`title: "Abel-Jacobi 与 Riemann-Roch 的证明"`），章节骨架：
1 出处与照录说明 → 2 记号与约定 → 3 定理 3.3.1（RR，含引理 3.3.2–3.3.4）→ 4 定理 3.5.4（双线性关系）→ 5 定理 3.5.9（Abel，含引理 3.5.10–3.5.12）→ 6 定理 3.5.13（Jacobi）→ 7 附：Gu 讲义对照 → 8 与主文的对应关系。

## Agent Extensions

### Skill

- **pdf**
- Purpose: 在缓存失效时重新抽取 5 份 Abel-Jacobi 文献与 Quad I/II/III 的文本，并核对待照录证明的原文位置。
- Expected outcome: 得到可逐句校对的纯文本（含页码标记），确保「严格照录」有原文依据。

### MCP

- **packpdf**
- Purpose: 用 `packpdf_check` 校验两篇 md 的公式规范、本地图片引用与 Jekyll `post_url` 引用是否成立。
- Expected outcome: 公式与链接零告警，新文章可被 PackPDF 正常收录为成稿。