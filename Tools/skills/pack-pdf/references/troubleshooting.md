# 故障排查

先看 `<PackPDF>/build/merged.log`，再按下表定位。

| 现象 / 日志关键词 | 原因 | 处理 |
|---|---|---|
| `Font "SimSun" not found` / `The font ... cannot be found` | 在 macOS/Linux 上用了 Windows 字体 | `export PACKPDF_CJK_FONT="Songti SC"` 或 `--font` 指定已安装字体 |
| `File 'xeCJK.sty' not found` | TeX 发行版缺少中文支持 | `sudo tlmgr install xecjk ctex fontspec` |
| `File 'fontspec.sty' not found` | 同上 | 安装 `fontspec`，或改用完整版 TeX Live / MacTeX |
| `pandoc: command not found` | 未安装或不在 PATH | 安装 pandoc；或设置 `PACKPDF_EXTRA_PATH` |
| `xelatex: command not found` | 未安装 TeX | 同上；MacTeX 路径通常是 `/Library/TeX/texbin` |
| `PDF 不完整或编译失败` | LaTeX 有错误但 nonstopmode 继续 | 看日志中 `^!` 行，多为公式写法问题 |
| `! Undefined control sequence` 指向 `\sub` | 非标准命令 | 改成 `\subset` / `\subseteq`，或用 `fix_math.py` |
| `! Missing $ inserted` | 公式与正文边界错乱，常见于 `$` 紧贴中文 | 给 `$` 前后加空格 |
| `! Extra }, or forgotten $` | `$$` 未配对 | 检查未闭合的公式块 |
| 中文变成空白 / 豆腐块 | 字体不含 CJK 字形 | 换字体，不要用纯西文字体 |
| 图片位置空白 | 图片路径解析失败 | `images scan` 检查文件是否存在；远程图确认可访问 |
| GIF 图片丢失 | 未安装 Pillow | `pip install Pillow` |
| `无法写入 PDF（权限被拒绝）` | PDF 被阅读器占用、或 OneDrive 同步中 | 关闭阅读器；工具会自动改存带时间戳的文件 |
| `TypeError: upload_and_replace() takes 1 positional argument` | GUI 用位置参数调用 keyword-only 接口 | 用本 Skill 的 `images upload`，它按关键字调用 |
| OSS `NoSuchKey` 之外的异常 | 网络或凭证问题 | 检查 AK/SK 与 bucket 地域；失败会自动重试 3 次 |
| 上传成功但页面还是旧图 | OSS 已有同名对象被跳过 | 加 `--force` 覆盖 |
| 目录里少了几篇 | 底层只读一层目录 | 把子目录作为独立输入，或传父目录让 Skill 展开 |
| PDF 里出现「暂存」「原文」等草稿 | 用了 `--all` 或 `published_only=false` 关闭了成稿筛选 | 去掉该开关（默认就只收成稿），先用 `--list-only` 核对名单 |
| 章与章接排在同一页 | 用了 `--page-break none` | 改回默认 `article` 或 `chapter` |
| 章号每个章节都从「第1章」重新开始 | 原实现按目录计数 | 本 Skill 已改为跨章连续编号 |
| 目录太长 / 太短 | TOC 深度固定为 1 | 需要调整时改 `packpdf/core.py` 的 `--toc-depth` |

## 排查顺序

1. `doctor`：确认工具与字体。
2. `check`：确认公式与图片。
3. `build --list-only`：确认入选名单与章节拆分。
4. `build`：失败看 `merged.log`。
5. `verify`：确认产物完整。
