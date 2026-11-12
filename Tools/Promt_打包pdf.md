## PDF 打包 Pipeline

思想：**先体检，后编译；规则归脚本，判断归人**。doctor 有 FAIL 就不要往下走，公式没查清就不要浪费一次 xelatex。

原始片段：

```
「先 packpdf_doctor 看看环境」
「把 _posts/1.Parameterization 按成稿文章打成 PDF」
「打包前先 packpdf_check 检查公式」
```

## 五步顺序

| 步 | 动作 | 命令 | 什么时候必须做 |
|---|---|---|---|
| 0 | 环境体检 | `packpdf_doctor` | 换机器、首次打包、报「找不到 pandoc/xelatex/字体」 |
| 1 | 公式与引用检查 | `packpdf_check` | 每次打包前，无例外 |
| 2 | 图片上传 | `packpdf_images_scan` → `packpdf_images_upload` | md 里有本地图片时 |
| 3 | 打名单 | `packpdf_build_pdf --list-only` | 换目录，或不确定哪些算成稿时 |
| 3.5 | 目录 | `packpdf_toc` | 只想更新 `目录.md`、暂不编译时；`build` 也会在编译前自动做一次 |
| 4 | 编译 | `packpdf_build_pdf` | 前三步无阻塞项 |
| 5 | 校验 | `packpdf_verify` | 每次编译后，不看体积页数不算交付 |

排查也按这个顺序走：体检 → 检查 → 名单 → 目录 → 编译 → 校验。

## 每步参数

**doctor**（只读）

| 参数 | 说明 |
|---|---|
| `font` | 指定中文字体，等价 `PACKPDF_CJK_FONT`；不填按平台默认 macOS `Songti SC` / Linux `Noto Serif CJK SC` / Windows `SimSun` |

产出：Python、PackPDF 路径、pandoc、xelatex、tectonic、中文字体（真实编译一次探测）、oss2、PyPDF2、Pillow。

**check**（只读）

| 参数 | 说明 |
|---|---|
| `paths` | md 文件或目录，多个 |
| `posts` | 额外检查 Jekyll `{% post_url %}`；非博客仓库不要开 |
| `max_issues` | 默认 20，问题多时调大 |

查 8 条公式规范（`$` 前后空格、公式内裸中文、行内 cases、`$$` 内空行、`\sub`、双重包裹、`$$` 配对、`\|` 范数）+ 图片引用是否存在。报告要给到**文件与行号**，只说「有问题」等于没查。

**images scan / upload**

| 参数 | 说明 |
|---|---|
| `apply` | 默认 false 仅预览；true 才上传并改写 md，自动生成 `.bak` |
| `force` | 同名同大小默认跳过；图更新过要覆盖才加 |
| `skip_missing` | 缺图默认中止；确认后才跳过，且结果里单独列出这些引用 |

凭证只从 `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` 读，不去翻 `config.json`。bucket 公读，图片会公开可访问，上传前要提醒。

**build**

| 参数 | 说明 |
|---|---|
| `paths` | 文件或目录；目录拆成「自身 + 一层子目录」当章节，底层不递归 |
| `output` | 默认落 `<PackPDF>/PDF_output/` |
| `title` | 文档标题 |
| `published_only` | **默认 true**：只收「文件名 `YYYY-MM-DD-*` **且** 带 frontmatter」的成稿，与路径是否含 `_posts` 无关 |
| `page_break` | **默认 `article`**：每篇另起页；`chapter` 仅每章另起页；`none` 不分页 |
| `list_only` | 只返回入选/排除清单，不编译，也不写目录 |
| `toc` | **默认 true**：编译前按成稿规则重建 `目录.md`（不存在则新建）；`false` 关闭 |
| `toc_title` | 新建目录时的首行书名，不填沿用已有目录 |
| `cover` | 封面图路径；不填自动找 `<路径>/0.前言/封面.jpg`；传空串表示不加封面 |
| `cover_fit` | **默认 `cover`**：居中裁剪成版心比例铺满；`contain` 保留原图、四周留白 |
| `font` | 覆盖字体 |

`--all`（CLI）或 `published_only=false`（MCP）是逃生舱，只在用户明确要打草稿排查时用，且要在结果里说明混进了哪些非成稿。

**verify**（只读）

体积 > 10KB、含 `%%EOF`、页数 > 0。失败看 `<PackPDF>/build/merged.log` 里 `^!` 开头的行。

## 五条常用提示词

```
「先 packpdf_doctor 看看环境，有 FAIL 先装依赖」
「打包前先 packpdf_check 检查 _posts/1.Parameterization 的公式，报文件和行号」
「把 _posts/1.Parameterization 按成稿文章打成 PDF，先 --list-only 给我看名单」
「图片先 scan，确认哪几张缺；没问题再 upload --apply」
「打完 packpdf_verify，回显绝对路径、页数、大小，以及排除了哪些文章」
「目录和正文要用同一批文章：build 前会按日期前缀 + frontmatter 重建 目录.md，别用旧目录」
「章和篇之间都要分页，用默认 page_break=article，跨章不许接排」
```

## 排版与命名

| 项 | 规则 |
|---|---|
| 章节标题 | 目录名 `1.基础曲面展开方法` → `第一章 基础曲面展开方法`；`0.前言` → `前言`，渲染为一级标题 |
| 文章标题 | 取 frontmatter `title:`，没有用文件名，渲染为二级标题（不进一级目录） |
| 分页 | 章标题前后各插 `\clearpage`：标题独占一页，该章正文次页起；章内第二篇起每篇另起页 |
| 二级标题 | 全部居中：文章标题 `\Large`、正文小标题 `\large` |
| 图片 | 注入 adjustbox，`max width=\linewidth` / `max height=0.85\textheight`，只缩不放 |
| md 目录 | **打包前**按成稿规则（日期前缀 + frontmatter）重建 `0.前言/目录.md`，缺失则新建；`--no-toc` 关闭，或单独 `toc` 子命令 |
| 封面 | 自动用 `<路径>/0.前言/封面.jpg`：裁剪成版心比例铺满一页，放在书名页与目录之前，封面页不计页码，正文从 1 开始 |
| 章导读 | 每章 `YYYY-MM-DD-导读.md` 固定排章内第一（与日期大小无关），紧跟章首页；缺或空占位会在日志里点名，0 字节文件不进 PDF |
| 章参考文献 | 每章 `参考文献.md` 固定排章末、总是另起一页；**不需要**日期前缀与 frontmatter；自带「参考文献」标题时不会重复注入 |
| 目录深度 | 固定为 1，只列章，页码即分页后的实际页码 |
| 输出被占用 | 自动改存带时间戳的文件名，必须在结果里说清楚 |

## 常见报错

| 现象 | 原因 | 处置 |
|---|---|---|
| `Font "SimSun" not found` | macOS/Linux 上用了 Windows 字体 | `--font "Songti SC"` 或设 `PACKPDF_CJK_FONT` |
| `File 'xeCJK.sty' not found` | TeX 缺中文支持 | `sudo tlmgr install xecjk ctex fontspec` |
| `pandoc/xelatex: command not found` | 不在 PATH | 装工具，或设 `PACKPDF_EXTRA_PATH`（MacTeX 在 `/Library/TeX/texbin`） |
| `! Undefined control sequence` 指向 `\sub` | 非标准命令 | 改 `\subset` / `\subseteq` |
| `! Missing $ inserted` | `$` 紧贴中文，公式边界错乱 | `$` 前后加空格 |
| `! Extra }, or forgotten $` | `$$` 未配对 | 找未闭合的公式块 |
| 中文变豆腐块 | 字体不含 CJK | 换字体，别用纯西文字体 |
| 图片位置空白 | 路径解析失败 | `images scan` 查存在性 |
| `无法写入 PDF` | 阅读器占用或同步盘 | 关阅读器；工具会改存时间戳文件 |
| 上传成功页面仍旧图 | OSS 同名对象被跳过 | 加 `force` |
| 少了几篇 | 底层只读一层目录 | 把子目录作为独立输入 |
| PDF 出现「暂存」「原文」 | 没开成稿筛选 | `published_only` + 先 `list_only` 核对 |

## 红线

- 只用用户指定的路径，**禁止默认扫描整个工作区**。
- 成稿判定「日期前缀 + frontmatter」缺一不可；不满足的只进排除清单，未经用户同意不得用 `--all` 收进来。唯一例外是章末 `参考文献.md`——它按约定直接进 PDF。
- 章导读与参考文献只按约定识别，缺失只提示不代写；0 字节占位一律不进 PDF。
- 上传图片、替换路径、批量改公式都写文件，必须显式 `apply` 且先备份。
- doctor 有 FAIL 不跳过直接编译；check 有公式问题先报告，不擅自全量 `fix_math`。
- 章导读按约定识别（日期后紧跟「导读」，旧名「介绍」兼容），缺失只提示不自动补写；不替作者生成正文内容。
- 不修改 PackPDF 源码，字体靠环境变量、筛选靠运行时包装。
- 中文路径与空格用参数列表传，不拼 shell 字符串。
- 交付只认「绝对路径 + 页数 + 大小」，有排除项说明原因。

## 暂不做

- 不让模型替人决定「哪篇算成稿」——名单先给人看。
- 不自动修公式：改错比不改更难查。
- 不做每步一个 MCP 工具的细分封装，调用顺序仍由本文件决定。
