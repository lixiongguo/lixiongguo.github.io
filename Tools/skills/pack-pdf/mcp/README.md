# PackPDF MCP Server

把 PackPDF 的打包能力暴露为 MCP 工具，供 Cursor、CodeBuddy 及其他支持 MCP 的客户端调用。

工具逻辑复用 `../scripts/pack.py`，与 Skill 共用一份实现。

## 工具清单

| 工具 | 作用 | 副作用 |
|---|---|---|
| `packpdf_doctor` | 检查 PackPDF 路径、pandoc、xelatex、tectonic、字体、依赖包 | 无 |
| `packpdf_check` | 公式规范 + 本地图片引用（可选 post_url 引用） | 无 |
| `packpdf_images_scan` | 列出本地图片引用及文件是否存在 | 无 |
| `packpdf_images_upload` | 上传到 OSS 并替换 md 路径 | `apply=true` 时改写文件 |
| `packpdf_build_pdf` | 合并编译 PDF | 写 `build/` 与输出 PDF |
| `packpdf_verify` | 校验 PDF 完整性 | 无 |

## 安装

需要一个装了 `mcp` 的 Python（3.10+）。推荐独立 venv，避免污染系统解释器：

```bash
cd Tools/skills/pack-pdf/mcp
python3 -m venv .venv
.venv/bin/python -m pip install -U "mcp>=1.2" "oss2>=2.18" "PyPDF2>=3.0" "Pillow>=9.0"
```

`oss2` 用于图片上传，`PyPDF2` 用于统计页数，`Pillow` 用于 GIF 转 PNG。缺哪个就少一项能力，`packpdf_doctor` 会逐项报告。

`server.py` 同时兼容 mcp 1.x（FastMCP）与 2.x（MCPServer）。

## 前置条件

MCP 只负责调用，**工具链必须装在运行 server 的那台机器上**：

- pandoc
- xelatex（TeX Live / MiKTeX / MacTeX）
- 中文字体（mac `Songti SC`、Windows `SimSun`、Linux `Noto Serif CJK SC`）
- 本仓库的 `Tools/PackPDF` 目录

先跑一次确认：

```bash
.venv/bin/python server.py --packpdf-home /path/to/Tools/PackPDF
# 另一个终端用任意 MCP 客户端调用 packpdf_doctor
```

## 配置

### Cursor

`~/.cursor/mcp.json`（全局）或项目下 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "packpdf": {
      "command": "/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/Tools/skills/pack-pdf/mcp/.venv/bin/python",
      "args": [
        "/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/Tools/skills/pack-pdf/mcp/server.py",
        "--packpdf-home",
        "/Users/lgxgeogo/Desktop/MyDoc/lixiongguo.github.io/Tools/PackPDF"
      ],
      "env": {
        "PACKPDF_CJK_FONT": "Songti SC"
      }
    }
  }
}
```

### CodeBuddy

设置 → MCP → Add MCP，内容同上（可加 `"type": "stdio"`）。

### Windows

```json
{
  "mcpServers": {
    "packpdf": {
      "command": "C:\\path\\to\\mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\skills\\pack-pdf\\mcp\\server.py",
               "--packpdf-home", "C:\\path\\to\\Tools\\PackPDF"],
      "env": { "PACKPDF_CJK_FONT": "SimSun" }
    }
  }
}
```

## 远程共享（多台机器）

在一台装了 TeX 的机器上以 HTTP 方式启动：

```bash
.venv/bin/python server.py \
  --transport streamable-http --host 0.0.0.0 --port 8765 \
  --packpdf-home /path/to/Tools/PackPDF
```

客户端填 URL 即可：

```json
{
  "mcpServers": {
    "packpdf": { "url": "http://<内网IP>:8765/mcp", "type": "http" }
  }
}
```

注意：

- 该接口能读写服务器文件、执行编译，**不要暴露到公网**；需要时加反向代理与鉴权。
- 编译目录 `PackPDF/build` 是共享的，服务端已用锁串行化 build，但多客户端同时打包仍会排队。

## 设计约束

- **stdout 只走协议**：`pack.py` 的 `print` 在调用期间被重定向到缓冲区，随返回值带回；启动日志写 stderr。
- **构建串行**：`packpdf_build_pdf` 持有进程内锁，避免并发写 `build/merged.md`。
- **写操作默认关闭**：`packpdf_images_upload` 默认 `apply=false`，只有显式传 `true` 才上传并改写 md，且自动生成 `.bak`。
- **密钥不进配置**：OSS 凭证只从环境变量读取，不要写进 `mcp.json`。
- **长任务**：整本书（30+ 篇）编译可能需要数分钟，客户端需放宽工具超时。
