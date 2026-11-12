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
    "no_toc": False,
    "toc_title": None,
    "cover": None,
    "no_cover": False,
    "cover_fit": "cover",
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
        "打包前会先按同一套成稿规则重建 markdown 目录（0.前言/目录.md），"
        "只想刷目录时调用 packpdf_toc；"
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
    "按成稿规则生成章节 markdown 目录（`# 书名 — 目录` + 每章 `## N. 章名` + `| 日期 | 文章 |` 表格）。"
    "只列「文件名带 YYYY-MM-DD 前缀且含 frontmatter」的文章，与 packpdf_build_pdf 的入选规则一致；"
    "published_only=false 时把草稿也列进去，日期列记 —。"
    "默认写到 <路径>/0.前言/目录.md（无 0.前言 时写 <路径>/目录.md），文件不存在则新建；"
    "book_title 不填则沿用已有目录首行书名，没有则用目录名。"
    "packpdf_build_pdf 在编译前会自动调用同一套逻辑，不需要先手动跑这个工具。"
))
def packpdf_toc(
    paths: list[str],
    output: str | None = None,
    book_title: str | None = None,
    published_only: bool = True,
) -> dict:
    result = _run(
        pack.cmd_toc,
        paths=paths,
        output=output,
        title=book_title,
        published_only=published_only,
        all=False,
    )
    m = re.search(r"目录: (.+)", result.get("log", ""))
    if m:
        result["toc"] = m.group(1).strip()
    return result


@server.tool(description=(
    "把 Markdown 编译成 PDF（pandoc + xelatex，两遍）。"
    "默认只收「文件名带 YYYY-MM-DD 前缀且含 frontmatter」的成稿文章，其余留在排除清单里；"
    "published_only=false 仅用于明确要求打包草稿的场景。"
    "编译前会按同一套规则重建 markdown 目录（toc=true，默认开；toc=false 关闭），"
    "这样 目录.md 与这次进 PDF 的文章始终一致。"
    "封面：默认自动找 <路径>/0.前言/封面.jpg；cover_fit=cover 居中裁剪成版心比例铺满（默认），"
    "contain 保留原图四周留白；cover=false 或 cover=\"\" 不加封面页。"
    "每章的「导读」（文件名 YYYY-MM-DD-导读.md，旧名 YYYY-MM-DD-介绍.md 仍兼容）固定排章内第一，紧跟章首页；"
    "每章的「参考文献」（文件名 参考文献.md，不需要日期前缀和 frontmatter）固定排章末并另起一页；"
    "两者缺失或只有 0 字节占位都会在日志里逐章点名（list_only 时看 intros / refs 字段）。"
    "章为一级标题、文章为二级标题，page_break 控制分页粒度"
    "（article=每篇另起页，默认；chapter=仅每章另起页；none=不分页）。"
    "list_only=true 只返回入选/排除清单，不编译也不写目录。"
))
def packpdf_build_pdf(
    paths: list[str],
    output: str | None = None,
    title: str | None = None,
    published_only: bool = True,
    page_break: str = "article",
    list_only: bool = False,
    font: str | None = None,
    toc: bool = True,
    toc_title: str | None = None,
    cover: str | None = None,
    cover_fit: str = "cover",
) -> dict:
    # cover 传空串表示不加封面页（None = 自动探测）
    no_cover = cover == ""
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
            no_toc=not toc,
            toc_title=toc_title,
            cover=cover or None,
            no_cover=no_cover,
            cover_fit=cover_fit,
        )
    log = result.get("log", "")
    m = re.search(r"成功: (.+?)（(.+?) 页，([\d.]+) KB）", log)
    if m:
        result["pdf"] = m.group(1)
        result["pages"] = int(m.group(2)) if m.group(2).isdigit() else m.group(2)
        result["size_kb"] = float(m.group(3))
    t = re.search(r"目录（打包前重建）: (.+?)（\d+ 篇）", log)
    result["toc"] = t.group(1).strip() if t else None
    c = re.search(r"封面: (.+?)（(\d+x\d+)）", log)
    result["cover"] = {"source": c.group(1), "source_size": c.group(2),
                       "fit": cover_fit} if c else None
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
