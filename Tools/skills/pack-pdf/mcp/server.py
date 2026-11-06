#!/usr/bin/env python3
"""PackPDF MCP Server — 把「Markdown 打包成 PDF」暴露为 MCP 工具。

支持 mcp SDK 1.x（FastMCP）与 2.x（MCPServer）。
工具逻辑全部复用 ../scripts/pack.py，不重复实现。

启动：
    python server.py                       # stdio（供 Cursor / CodeBuddy 拉起）
    python server.py --transport streamable-http --port 8765   # 给别的机器远程调用
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import sys
import threading
from argparse import Namespace
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "scripts"))

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server

    _SDK_MAJOR = 2
except ImportError:  # mcp < 2.0
    from mcp.server.fastmcp import FastMCP as _Server

    _SDK_MAJOR = 1

import pack  # noqa: E402

BUILD_LOCK = threading.Lock()

_DEFAULTS = {
    "paths": [],
    "output": None,
    "title": None,
    "font": None,
    "published_only": True,
    "all": False,
    "page_break": "article",
    "list_only": False,
    "max_issues": 40,
    "json": False,
    "posts": False,
    "apply": False,
    "dry_run": True,
    "force": False,
    "skip_missing": False,
    "pdf": "",
}

server = _Server(
    "packpdf",
    instructions=(
        "把 Markdown 文章或章节目录打包成 PDF。"
        "动手前先调用 packpdf_doctor 检查 pandoc / xelatex / 字体；"
        "默认只打成稿文章（文件名带 YYYY-MM-DD 前缀且含 frontmatter），其余进排除清单；"
        "章为一级标题、文章为二级标题，章与章之间、篇与篇之间自动分页；"
        "有本地图片时先 packpdf_images_scan，再用 packpdf_images_upload(apply=true) 上传替换。"
    ),
)


def _run(fn, **kwargs) -> dict:
    """调用 pack.py 的 cmd_*，把 stdout 收进返回值。

    stdio 传输时 stdout 是协议通道，pack.py 里的 print 必须整体重定向，
    否则会把 JSON-RPC 流冲坏。
    """
    ns = Namespace(**{**_DEFAULTS, **kwargs})
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = int(fn(ns) or 0)
    except SystemExit as exc:
        return {"ok": False, "exit_code": 2, "error": str(exc), "log": buf.getvalue()[-8000:]}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "exit_code": 1,
            "error": f"{type(exc).__name__}: {exc}",
            "log": buf.getvalue()[-8000:],
        }
    return {"ok": code == 0, "exit_code": code, "log": buf.getvalue()[-8000:]}


@server.tool(description="检查运行环境：PackPDF 路径、pandoc、xelatex、tectonic、中文字体、oss2/PyPDF2/Pillow。打包前先调用。")
def packpdf_doctor(font: str | None = None) -> dict:
    return _run(pack.cmd_doctor, font=font)


@server.tool(description="检查 Markdown 的公式规范与本地图片引用。paths 可以是 .md 文件或目录列表。posts=true 时额外检查 Jekyll 的 post_url 引用。")
def packpdf_check(paths: list[str], posts: bool = False, max_issues: int = 20) -> dict:
    return _run(pack.cmd_check, paths=paths, posts=posts, max_issues=max_issues)


@server.tool(description="列出文档中的本地图片引用，以及文件是否存在。只读，不上传。")
def packpdf_images_scan(paths: list[str]) -> dict:
    return _run(pack.cmd_images_scan, paths=paths)


@server.tool(description="把本地图片上传到 OSS 图床并替换 md 里的路径。apply=false 仅预览；apply=true 才真正上传并改写文件（自动生成 .bak 备份）。凭证从环境变量 OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET 读取。")
def packpdf_images_upload(
    paths: list[str],
    apply: bool = False,
    force: bool = False,
    skip_missing: bool = False,
) -> dict:
    return _run(
        pack.cmd_images_upload,
        paths=paths,
        apply=apply,
        dry_run=not apply,
        force=force,
        skip_missing=skip_missing,
    )


@server.tool(description=(
    "把 Markdown 编译成 PDF（pandoc + xelatex，两遍）。"
    "默认只收「文件名带 YYYY-MM-DD 前缀且含 frontmatter」的成稿文章，其余留在排除清单里；"
    "published_only=false 仅用于明确要求打包草稿的场景。"
    "章为一级标题、文章为二级标题，page_break 控制分页粒度"
    "（article=每篇另起页，默认；chapter=仅每章另起页；none=不分页）。"
    "list_only=true 只返回入选/排除清单，不编译。"
))
def packpdf_build_pdf(
    paths: list[str],
    output: str | None = None,
    title: str | None = None,
    published_only: bool = True,
    page_break: str = "article",
    list_only: bool = False,
    font: str | None = None,
) -> dict:
    # 同一时刻只允许一个编译，避免并发写 build/merged.md
    with BUILD_LOCK:
        result = _run(
            pack.cmd_build,
            paths=paths,
            output=output,
            title=title,
            font=font,
            published_only=published_only,
            page_break=page_break,
            all=False,
            list_only=list_only,
        )
    m = re.search(r"成功: (.+?)（(.+?) 页，([\d.]+) KB）", result.get("log", ""))
    if m:
        result["pdf"] = m.group(1)
        result["pages"] = int(m.group(2)) if m.group(2).isdigit() else m.group(2)
        result["size_kb"] = float(m.group(3))
    return result


@server.tool(description="校验生成的 PDF：体积、%%EOF 结束标记、页数。")
def packpdf_verify(pdf: str) -> dict:
    return _run(pack.cmd_verify, pdf=pdf)


def main() -> None:
    ap = argparse.ArgumentParser(description="PackPDF MCP Server")
    ap.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--packpdf-home", default="", help="PackPDF 目录，等同于 PACKPDF_HOME")
    ap.add_argument("--font", default="", help="中文字体，等同于 PACKPDF_CJK_FONT")
    args = ap.parse_args()

    if args.packpdf_home:
        os.environ["PACKPDF_HOME"] = args.packpdf_home
    if args.font:
        os.environ["PACKPDF_CJK_FONT"] = args.font

    # 启动信息只能写 stderr，stdout 留给协议
    print(f"[packpdf-mcp] sdk={_SDK_MAJOR} transport={args.transport}", file=sys.stderr)

    if args.transport == "stdio":
        server.run()
    elif _SDK_MAJOR >= 2:
        server.run(transport=args.transport, host=args.host, port=args.port)
    else:  # mcp 1.x：host/port 在 settings 上
        server.settings.host = args.host
        server.settings.port = args.port
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
