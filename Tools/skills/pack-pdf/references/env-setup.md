# 环境准备

## 必须组件

| 组件 | 用途 | 缺失后果 |
|---|---|---|
| Python 3.9+ | 编排 | 无法运行 |
| pandoc | Markdown → LaTeX | 编译直接失败 |
| xelatex（TeX Live / MiKTeX / MacTeX） | LaTeX → PDF | 章节模式失败 |
| 含 CJK 的字体 | 中文排版 | fontspec 报字体不存在 |
| oss2 | 上传 OSS | 图片步骤不可用（可选） |
| PyPDF2 | 统计页数 | 页数显示未知（可选） |
| Pillow | GIF 转 PNG | GIF 图片会丢失（可选） |

`tectonic` 只有整本专著模式（`build_monograph.py`）需要，章节模式不需要。

## macOS

```bash
brew install pandoc
brew install --cask mactex-no-gui     # 约 2GB，含 xeCJK / fontspec
# 或：brew install --cask basictex，再补包
sudo tlmgr update --self
sudo tlmgr install xecjk ctex fontspec unicode-math

python3 -m pip install oss2 PyPDF2 Pillow
```

字体：mac 自带 `Songti SC`、`STSong`，**没有** `SimSun`（宋体是 Windows 字体）。
默认使用 `Songti SC`；要换字体：

```bash
export PACKPDF_CJK_FONT="STSong"
```

代码块另有一套字体：西文默认 `Menlo`，中文沿用上面的 CJK 字体。
**不要用 Latin Modern Mono**——它没有希腊字母，代码里的 `π` 会被静默丢掉
（`k * π / 2` 渲染成 `k * /2`）。要换：

```bash
export PACKPDF_MONO_FONT="DejaVu Sans Mono"
```

## Windows

- 安装 [Pandoc](https://pandoc.org/installing.html)。
- 安装 MiKTeX 或 TeX Live（需含 `xelatex`、`xeCJK`）。
- 字体默认 `SimSun`，系统自带。

```powershell
pip install -r requirements.txt
$env:PACKPDF_EXTRA_PATH = "C:\Program Files\Pandoc;C:\Program Files\MiKTeX\miktex\bin\x64"
```

## Linux

```bash
sudo apt install pandoc texlive-xetex texlive-lang-chinese fonts-noto-cjk
pip install oss2 PyPDF2 Pillow
export PACKPDF_CJK_FONT="Noto Serif CJK SC"
```

## 环境变量

| 变量 | 作用 |
|---|---|
| `PACKPDF_HOME` | PackPDF 目录（含 `packpdf/`），用于定位工具 |
| `PACKPDF_CJK_FONT` | 中文字体名，覆盖平台默认值 |
| `PACKPDF_MONO_FONT` | 代码块西文字体名，默认 Menlo / DejaVu Sans Mono / Consolas；必须含希腊字母 |
| `PACKPDF_EXTRA_PATH` | 追加到 PATH 的工具目录，`;` 或 `:` 分隔 |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` | 阿里云 OSS 凭证，仅上传图片时使用 |

## 验证

```bash
python scripts/pack.py doctor
```

全部 OK（字体一项为 `SKIP` 时说明没装 xelatex）即可开始打包。
