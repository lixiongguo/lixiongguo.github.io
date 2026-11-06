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

检查 8 条公式规范（`$` 前后空格、公式内裸中文、行内 cases、`$$` 内空行、`\sub`、双重包裹、`$$` 配对、`\|` 范数）以及图片引用是否存在。

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

```bash
# 已成稿文章（文件名带日期前缀 + 有 frontmatter），适合 _posts
python scripts/pack.py build <PATH...> --published-only -o book.pdf

# 普通笔记（无日期前缀、无 frontmatter）
python scripts/pack.py build <PATH...> -o notes.pdf

# 调试：只列入选/排除清单，不编译
python scripts/pack.py build <PATH...> --published-only --list-only
```

输入路径中含 `_posts` 时默认启用 `--published-only`；`--all` 可覆盖。

「已成稿」判定 = 文件名匹配 `YYYY-MM-DD-*.md` **且** 文件开头有 YAML frontmatter，等价于 Jekyll 会真正渲染的文章。

### 5. 校验

```bash
python scripts/pack.py verify <out.pdf>
```

确认体积 > 10KB、含 `%%EOF`、页数 > 0。失败时查看 `<PackPDF>/build/merged.log` 中 `^!` 开头的行。

## 输出与参数

| 项 | 说明 |
|---|---|
| 章节标题 | 目录名 `1.基础曲面展开方法` → `第一章 基础曲面展开方法`；`0.前言` → `前言` |
| 文章标题 | 取 frontmatter 的 `title:`，没有则用文件名 |
| 编号 | 跨章节连续编号（`第1章` 起累加） |
| 中文字体 | 默认 macOS `Songti SC`、Linux `Noto Serif CJK SC`、Windows `SimSun`，可用 `--font` 覆盖 |
| 输出默认位置 | `<PackPDF>/PDF_output/` |
| 输出被占用 | 底层自动改存带时间戳的文件名，需在结果中明确告知 |

## 约束

- **不修改 PackPDF 源码**；筛选与编号通过运行时包装实现，字体通过 `PACKPDF_CJK_FONT` 环境变量传入。
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
