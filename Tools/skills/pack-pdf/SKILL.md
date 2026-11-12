---
name: pack-pdf
description: 把 Markdown 文章或章节目录打包成 PDF，并在打包前检查公式规范、把本地图片上传到 OSS 图床、替换 md 中的图片路径。当用户要求把笔记/文章/整本书生成或重新生成 PDF、合并多个章节、导出可打印文档，或提到 PackPDF、pandoc、xelatex、PDF 编译失败、图片没上传时使用。
---

# PackPDF 文档打包

将 Markdown 编译为可交付 PDF。编译链是 pandoc → LaTeX → xelatex（两遍，用于目录页码）。

底层工具位于本机某处的 `Tools/PackPDF`，本 Skill 只做编排，不复制其实现。

## 先定位工具

```bash
python scripts/pack.py doctor
```

`doctor` 会检查 Python、PackPDF 路径、pandoc、xelatex、tectonic、中文字体（用 xelatex 真实编译一次探测）、oss2、PyPDF2、Pillow。

- 有 FAIL 时先按 `references/env-setup.md` 安装，不要跳过直接编译。
- 找不到 PackPDF 时设置 `PACKPDF_HOME`，指向包含 `packpdf/` 的目录。

## 标准流程

### 1. 明确输入

只用用户指定的文件或目录，**禁止默认扫描整个工作区**（大型仓库可能有数百个无关 md）。

单文件、目录都可以；目录会被拆成「自身 + 一层子目录」作为章节，因为底层工具不递归。

### 2. 检查

```bash
python scripts/pack.py check <PATH...>
```

检查 9 条公式规范（`$` 前后空格、公式内裸中文、行内 cases、`$$` 内空行、`\sub`、双重包裹、`$$` 配对、`\|` 范数、**句中 `$$`**）以及图片引用是否存在。

第 9 条最容易漏：`$$...$$` 是块级公式，会独占一行居中。写在句子里（`即$$U=0$$的常映射`）会把整段话切成碎片，PDF 里表现为"我们将 / 分块为 / 其中"各占一行。判定时排除代码块与合法的整行 `$$`。

- 有公式问题先报告文件与行号；需要自动修复时使用 PackPDF 的 `fix_math.py`，**修改前先备份**。
- `--posts` 才检查 Jekyll 的 `{% post_url %}` 引用，非博客仓库不要加。

### 3. 图片上传（有本地图片时必做）

```bash
python scripts/pack.py images scan <PATH...>
python scripts/pack.py images upload <PATH...>            # 预览，不改文件
python scripts/pack.py images upload <PATH...> --apply    # 上传并替换路径
```

规则：

- 凭证只从 `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` 读取。**不要读取** `config.json` 或 `docs/AccessKey.csv`；缺少凭证时直接告诉用户设置环境变量。
- 默认 dry-run；`--apply` 才上传与改写，并自动生成 `<file>.md.bak`。
- 已有同名对象且大小一致时跳过；本地图更新过、需要覆盖时加 `--force`。
- 缺图默认中止；用户确认后加 `--skip-missing` 继续，并在结果中单独列出这些引用。
- 提醒用户：该 bucket 公读，图片会公开可访问。

无本地图片时跳过本步。

### 4. 打包

默认就只打成稿文章，不需要额外开关：

```bash
# 成书（默认：仅日期前缀 + frontmatter 的文章；章与篇之间自动分页；编译前重建目录）
python scripts/pack.py build <PATH...> -o book.pdf

# 分页粒度：article=每篇另起页（默认）/ chapter=仅每章另起页 / none=不分页
python scripts/pack.py build <PATH...> --page-break chapter -o book.pdf

# 调试：只列入选/排除清单，不编译
python scripts/pack.py build <PATH...> --list-only

# 封面：自动用 <PATH>/0.前言/封面.jpg，居中裁剪成版心比例铺满
python scripts/pack.py build <PATH...> --cover 封面.png      # 指定别的图
python scripts/pack.py build <PATH...> --cover-fit contain   # 不裁剪，四周留白
python scripts/pack.py build <PATH...> --no-cover            # 不要封面页

# 例外：连草稿一起打，仅用户明确要求时用
python scripts/pack.py build <PATH...> --all -o drafts.pdf
```

「已成稿」判定 = 文件名匹配 `YYYY-MM-DD-*.md` **且** 文件开头有 YAML frontmatter，等价于 Jekyll 会真正渲染的文章。缺任一条都进排除清单并注明原因，与路径是否含 `_posts` 无关。

版式：目录名 → `#` 章标题（一级），frontmatter `title` → `##` 节标题（二级）。

- 章首页：标题垂直居中、26pt 加粗、下方一条 0.42 倍版心宽细线，前后各分页，该章正文从下一页开始
- 二级标题：全部居中，文章标题 `\Large`，正文小标题 `\large`（文章标题在合并时带 `<!--art-->` 标记，处理完即删）
- 书名：只由 `\maketitle` 打印，不再生成 `\section`，目录里不会重复出现
- 图片：注入 `\usepackage[export]{adjustbox}` + `max width=\linewidth, max height=0.85\textheight`，只缩不放，避免大图溢出压住正文
- 代码块里的 `#` 注释不会被当作标题

编译前会自动重建 markdown 目录（详见下节），`--no-toc` 关闭，`--toc-title` 指定新建时的书名。

### 4.1 目录（markdown）

```bash
# 只重建目录，不编译（改完文章 / 只想要目录时用）
python scripts/pack.py toc <PATH...>
python scripts/pack.py toc <PATH...> -o 目录.md --title "1. 参数化"
```

时机：**先建目录，再编译**。`build` 在调用 pandoc 之前按同一套成稿规则（日期前缀 + frontmatter）重建目录，保证 `目录.md` 里列的正是这次进 PDF 的那批文章；`--list-only` 只列名单，不写目录。只想刷目录不编译时用 `toc` 子命令。

输出默认落在 `<PATH>/0.前言/目录.md`（`0.前言` 目录存在时，没有该文件也会新建），否则 `<PATH>/目录.md`。格式：`# 书名 — 目录` + 每章 `## N. 章名` + `| 日期 | 文章 |` 表格，末尾统计篇数。书名沿用已有文件首行，不会每次改写；新建时用 `--title`/`--toc-title`，都不填则用目录名。

细节：文件名没有日期前缀的（只有 `--all` 时才会出现）日期列记 `—` 并在末尾单列数量；整章没有可列文章时整节省略；标题里的 `|` 会转义，避免把表格行劈开。

### 4.2 封面

`build` 会自动找封面图：`<PATH>/0.前言/封面.jpg`（也认 `cover.*`、`png/webp/bmp`），找到就加一页整版封面，放在 `\maketitle` 与目录之前。`--cover <path>` 指定其它图，`--no-cover` 关闭。

- `--cover-fit cover`（默认）：用 Pillow 居中裁剪成**版心**比例，再铺满版心，四周仍是 2.5cm 白边。横图会被切掉左右多余部分，构图主体居中。
- `--cover-fit contain`：不裁剪，原图等比缩到版心内居中，四周白边更大。
- 裁剪结果落在 `<PackPDF>/build/cover/cover.jpg`（ASCII 路径，避免中文路径进 `graphicx`），质量 92，原图不动。
- 封面页不显示页码，其后 `\setcounter{page}{1}`，正文从 1 开始编号。

**不要用 `\newgeometry{margin=0pt}` 做无边满版**：它在 `\begin{document}` 后会先 `\clearpage`，凭空多一张空白页，`\thispagestyle` 还会落到那张空页上，页码跟着串（已踩过）。图高也不能取满 `\textheight`，会溢出约 7pt 再产生一张空白页，所以按 0.985 倍取。

### 4.3 章导读

约定：每章开头一篇 `YYYY-MM-DD-导读.md`（日期后**紧跟**「导读」；旧名 `YYYY-MM-DD-介绍.md` 仍兼容，`2016-07-14-共形映射介绍.md`、`2018-05-01-最优传输介绍.md` 这类正文不算）。

- 排序：导读永远排章内第一，与日期大小无关（`2020-06-01-导读.md` 也会排在 `2019-05-01-xxx.md` 前面）；其余文章按文件名升序（日期前缀即时间序）。
- 位置：紧跟章首页，成为该章第一篇；`page_break=article` 时它不另起页，正好当本章开篇。
- 检查：`build` 逐章报告导读状态 —— `导读: xxx.md`、`导读占位未写`、`导读缺 frontmatter`、`缺少导读`，末尾汇总「导读待补 N 章」；`--list-only --json` 的 `intros` 字段给结构化结果。
- 0 字节占位文件一律不进 PDF，排除原因写「空文件（占位，未写内容）」，`--all` 也一样。

### 4.4 章参考文献

约定：每章一个 `参考文献.md`（也认 `YYYY-MM-DD-参考文献.md`），固定排章末。

- **不受成稿规则约束**：没有日期前缀、没有 frontmatter 也照样进 PDF —— 它是章节附件，不是 Jekyll 文章。换成别的文件名（如 `refs.md`）就不认，得按普通文章加日期前缀 + frontmatter。
- 排序：导读 → 正文（按文件名）→ 参考文献；参考文献**总是另起一页**，即使 `--page-break chapter`。
- 标题：文件里已有 `#`/`##`/`### 参考文献` 就直接用，没有就按文件名注入居中的「参考文献」，不会出现两个标题。
- 0 字节占位不进 PDF，逐章提示「参考文献占位未写」；`build` 末尾汇总「参考文献待补 N 章」，`--list-only --json` 看 `refs` 字段。
- `目录.md` 里该章表格最后一行是 `| — | [参考文献](参考文献.md) |`，不计入篇数。

### 5. 校验

```bash
python scripts/pack.py verify <out.pdf>
```

确认体积 > 10KB、含 `%%EOF`、页数 > 0。失败时查看 `<PackPDF>/build/merged.log` 中 `^!` 开头的行。

## 输出与参数

| 项 | 说明 |
|---|---|
| 章节标题 | 目录名 `1.基础曲面展开方法` → `第一章 基础曲面展开方法`；`0.前言` → `前言` |
| 文章标题 | 取 frontmatter 的 `title:`，没有则用文件名；渲染为居中的二级标题 |
| 分页 | `--page-break article`（默认）每篇另起页；`chapter` 仅每章另起页；`none` 不分页 |
| PDF 目录 | `--toc-depth=1`，只列章 + 前言，条目即分页后的实际页码，标题为「目录」 |
| md 目录 | **打包前**按成稿规则重建 `目录.md`（不存在则新建），`--no-toc` 关闭；也可单独跑 `toc` 子命令 |
| 封面 | 自动找 `<PATH>/0.前言/封面.jpg`；`--cover-fit cover`（默认，裁剪铺满版心）/ `contain`（留白）；`--no-cover` 关闭 |
| 章导读 | 每章 `YYYY-MM-DD-导读.md` 固定排章内第一；缺/空占位会在打包日志里点名，空文件不进 PDF |
| 章参考文献 | 每章 `参考文献.md` 固定排章末、另起一页，不需要日期前缀与 frontmatter；缺/空占位同样点名 |
| 中文字体 | 默认 macOS `Songti SC`、Linux `Noto Serif CJK SC`、Windows `SimSun`，可用 `--font` 覆盖 |
| 代码块字体 | 西文 Menlo / DejaVu Sans Mono / Consolas（须含希腊字母），中文同 CJK 字体；可用 `PACKPDF_MONO_FONT` 覆盖 |
| 输出默认位置 | `<PackPDF>/PDF_output/` |
| 输出被占用 | 底层自动改存带时间戳的文件名，需在结果中明确告知 |

## 约束

- **不复制 PackPDF 的实现**；筛选、层级与分页通过运行时包装实现。
- 字体通过环境变量传入（`PACKPDF_CJK_FONT` / `PACKPDF_MONO_FONT`）。代码块的中西文等宽字体由 `packpdf/core.py` 的 `_fix_latex` 在编译前注入——Latin Modern Mono 缺希腊字母，代码里的 `π` 会被静默丢弃，这个修正必须留在管线内部而不是靠调用方传参。
- 默认只打成稿；`--all` 只在用户明确要求打包草稿时使用，并在结果里说明混入了哪些非成稿文件。
- 上传、替换路径、自动修复公式都会写文件，必须显式 `--apply`，且先备份。
- 中文路径与空格一律用参数列表传递，不拼接 shell 字符串。
- 交付结果时回显绝对路径、页数、大小；有排除项时说明原因。

## MCP（可选）

需要在 Cursor、Claude Desktop 或其他机器上调用时，使用 `mcp/server.py`，配置见 `mcp/README.md`。

- MCP 与 Skill 共用 `scripts/pack.py`，**不要另写一份实现**。
- MCP 工具粒度更细（doctor/check/images/build/verify），不携带本文件里的流程决策；调用顺序仍按本文档。
- 远程模式（`--transport streamable-http`）只在内网使用，接口可读写服务器文件。

## 故障排查

见 `references/troubleshooting.md`。常见：字体缺失、`xeCJK.sty` 找不到、图片丢失、`PermissionError`、PDF 不完整。
