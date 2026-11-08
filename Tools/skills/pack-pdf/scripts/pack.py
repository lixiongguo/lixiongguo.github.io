#!/usr/bin/env python3
"""PackPDF Skill 统一入口。

子命令：
    doctor                         环境与依赖体检
    check      PATH...             公式规范 / post_url / 图片检查（只读）
    images scan    PATH...         列出文档中的本地图片引用
    images upload  PATH...         上传 OSS 并替换 md 路径（默认 dry-run）
    build      PATH...             合并编译 PDF
    verify     PDF                 校验产物

约定：
    - 不改写 PackPDF 源码（字体通过环境变量 PACKPDF_CJK_FONT 传入）。
    - 所有写操作默认关闭，需显式 --apply。
    - 密钥只从环境变量读取，不读 config.json / AccessKey.csv。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, unquote

OSS_ENDPOINT = "https://oss-cn-beijing.aliyuncs.com"
OSS_BUCKET = "lgximgs"
OSS_KEY_PREFIX = "images/"
OSS_BASE = "https://lgximgs.oss-cn-beijing.aliyuncs.com/images/"

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "_site", "build", "dist",
    "__pycache__", "PDF_output", ".codebuddy", ".pytest_cache",
}

DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
FRONTMATTER = re.compile(r"^---\r?\n.+?\r?\n---\s*(\r?\n|$)", re.DOTALL)
MD_IMG = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
HTML_IMG = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
TITLE_RE = re.compile(r"^title:\s*[\"']?(.+?)[\"']?\s*$", re.M)

CN_DIGITS = "零一二三四五六七八九"


# ── 基础工具 ────────────────────────────────────────────────


def die(msg: str, code: int = 2) -> int:
    print(msg, file=sys.stderr)
    return code


def default_font() -> str:
    if sys.platform == "darwin":
        return "Songti SC"
    if sys.platform.startswith("linux"):
        return "Noto Serif CJK SC"
    return "SimSun"


def natural_key(name: str):
    """按目录名前导数字排序：0.前言 < 1.基础 < 2.共形 < 10.附录。"""
    m = re.match(r"^(\d+)", name)
    return (0, int(m.group(1)), name) if m else (1, 0, name)


def _cn(n: int) -> str:
    if n < 10:
        return CN_DIGITS[n]
    if n < 20:
        return "十" + (CN_DIGITS[n % 10] if n % 10 else "")
    return CN_DIGITS[n // 10] + "十" + (CN_DIGITS[n % 10] if n % 10 else "")


def chapter_label(name: str) -> str:
    m = re.match(r"^(\d+)[.、_\-\s]*(.*)$", name)
    if not m:
        return name
    n, rest = int(m.group(1)), m.group(2).strip()
    if n == 0:
        return rest or "前言"
    return f"第{_cn(n)}章 {rest}".strip()


# ── 文件发现与成稿判定 ──────────────────────────────────────


def iter_md(paths) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_file():
            if p.suffix.lower() in (".md", ".markdown"):
                found.append(p)
            continue
        if not p.is_dir():
            print(f"[跳过] 路径不存在: {p}")
            continue
        for f in sorted(p.rglob("*.md")):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            found.append(f)
    return found


def has_frontmatter(path: Path) -> bool:
    try:
        head = path.read_text("utf-8")[:8192].lstrip("\ufeff")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(FRONTMATTER.match(head))


def is_published(path: Path | str) -> bool:
    p = Path(path)
    return bool(DATE_PREFIX.match(p.name)) and has_frontmatter(p)


def exclude_reason(path: Path) -> str:
    if not DATE_PREFIX.match(path.name):
        return "缺少日期前缀"
    if not has_frontmatter(path):
        return "缺少 frontmatter"
    return ""


# ── PackPDF 定位与加载 ──────────────────────────────────────


def find_packpdf() -> Path | None:
    cands: list[Path] = []
    env = os.environ.get("PACKPDF_HOME", "").strip()
    if env:
        cands.append(Path(env).expanduser())
    here = Path.cwd()
    for base in [here, *here.parents]:
        cands.append(base / "Tools" / "PackPDF")
        cands.append(base / "PackPDF")
    cands.extend([
        Path.home() / "Desktop/MyDoc/lixiongguo.github.io/Tools/PackPDF",
        Path.home() / "lixiongguo.github.io/Tools/PackPDF",
    ])
    for c in cands:
        if (c / "packpdf" / "core.py").exists():
            return c.resolve()
    return None


def load_packpdf() -> Path:
    root = find_packpdf()
    if root is None:
        raise SystemExit(
            "未找到 PackPDF。请设置 PACKPDF_HOME 指向包含 packpdf/ 的目录，"
            "例如 export PACKPDF_HOME=~/Desktop/MyDoc/lixiongguo.github.io/Tools/PackPDF"
        )
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


# ── doctor ─────────────────────────────────────────────────


def probe_font(font: str) -> bool:
    """用 xelatex 编译最小文档，真实验证字体是否存在。"""
    tex = (
        "\\documentclass{article}\n"
        "\\usepackage{xeCJK}\n"
        f"\\setCJKmainfont{{{font}}}\n"
        "\\begin{document}测试\\end{document}\n"
    )
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "probe.tex").write_text(tex, encoding="utf-8")
        r = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "probe.tex"],
            cwd=td, capture_output=True,
        )
        return r.returncode == 0 and (Path(td) / "probe.pdf").exists()


def cmd_doctor(args) -> int:
    rows: list[dict] = []

    def add(name: str, ok, detail: str) -> None:
        rows.append({"name": name, "ok": ok, "detail": detail})

    add("python", sys.version_info >= (3, 9), sys.version.split()[0])
    root = find_packpdf()
    add("packpdf", root is not None, str(root) if root else "未找到（设置 PACKPDF_HOME）")

    if root is not None:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from packpdf.deps import ensure_toolchain_path  # noqa: WPS433
        ensure_toolchain_path()

    pandoc = shutil.which("pandoc")
    xelatex = shutil.which("xelatex")
    tectonic = shutil.which("tectonic")
    add("pandoc", bool(pandoc), pandoc or "未安装")
    add("xelatex", bool(xelatex), xelatex or "未安装（章节模式必需）")
    add("tectonic", bool(tectonic), tectonic or "未安装（仅专著模式需要）")

    font = args.font or os.environ.get("PACKPDF_CJK_FONT") or default_font()
    if xelatex:
        ok = probe_font(font)
        add(f"字体 {font}", ok, "可用" if ok else "xelatex 无法加载该字体")
    else:
        add(f"字体 {font}", None, "跳过（无 xelatex）")

    for mod, pkg in (("oss2", "oss2"), ("PyPDF2", "PyPDF2"), ("PIL", "Pillow")):
        try:
            __import__(mod)
            add(mod, True, "已安装")
        except ImportError:
            add(mod, False, f"缺少：pip install {pkg}")

    ok_req = True
    for row in rows:
        if row["ok"] is None:
            mark = "SKIP"
        elif row["ok"]:
            mark = "OK  "
        else:
            mark = "FAIL"
            if row["name"] in ("python", "packpdf", "pandoc", "xelatex"):
                ok_req = False
        print(f"[{mark}] {row['name']:<18} {row['detail']}")

    if args.json:
        print(json.dumps({"checks": rows}, ensure_ascii=False, indent=2))

    if not ok_req:
        print("\n缺失必需依赖时请先安装：见 references/env-setup.md")
        return 2
    return 0


# ── check ──────────────────────────────────────────────────


def cmd_check(args) -> int:
    load_packpdf()
    from packpdf import math_check

    files = iter_md(args.paths)
    if not files:
        return die("未找到 .md 文件")

    issues_total = 0
    bad_files = 0
    report = []
    for f in files:
        issues = math_check.check_file(str(f))
        if not issues:
            continue
        bad_files += 1
        issues_total += len(issues)
        for it in issues:
            report.append({
                "file": str(f),
                "line": it.line,
                "rule": it.rule.title,
                "detail": it.detail,
                "snippet": it.snippet_text(),
            })

    images = scan_images(files)
    missing_images = [i for i in images if not i["exists"]]

    print(f"扫描 {len(files)} 个文件")
    if issues_total:
        print(f"公式问题：{bad_files} 个文件 / {issues_total} 处")
        for r in report[: args.max_issues]:
            loc = f"L{r['line']}" if r["line"] else "EOF"
            print(f"  {r['file']}:{loc}  {r['rule']}  {r['detail']}")
            if r["snippet"]:
                print(f"      {r['snippet']}")
        if len(report) > args.max_issues:
            print(f"  ... 其余 {len(report) - args.max_issues} 处省略")
    else:
        print("公式规范：全部通过")

    print(f"本地图片引用：{len(images)} 处，缺失 {len(missing_images)} 处")
    for i in missing_images[:20]:
        print(f"  [缺失] {i['raw']}  ← {i['md']}")

    broken = 0
    if args.posts:
        from packpdf import post_check
        result = post_check.check_directory(str(Path(args.paths[0]).resolve()))
        broken = result.total_broken
        print(f"post_url 引用：断裂 {broken} 处")
        for fr in result.files:
            for br in fr.broken:
                print(f"  {fr.path}:{br.ref.line}  {br.ref.slug}")

    if args.json:
        print(json.dumps({
            "files": len(files),
            "formula_files": bad_files,
            "formula_issues": issues_total,
            "image_refs": len(images),
            "image_missing": len(missing_images),
            "post_url_broken": broken,
            "issues": report,
        }, ensure_ascii=False, indent=2))

    return 1 if (issues_total or broken) else 0


# ── images ─────────────────────────────────────────────────


def is_remote(path_str: str) -> bool:
    s = path_str.strip()
    return s.startswith(("http://", "https://", "//", "data:"))


def find_imgs_dir(md: Path) -> Path | None:
    for base in [md.parent, *md.parents]:
        cand = base / "imgs"
        if cand.is_dir():
            return cand
    return None


def resolve_image(md: Path, raw: str) -> Path:
    clean = unquote(raw.split("#")[0].split("?")[0])
    if os.path.isabs(clean):
        return Path(clean)
    direct = md.parent / clean
    if direct.exists():
        return direct.resolve()
    imgs = find_imgs_dir(md)
    if imgs is not None:
        alt = imgs / Path(clean).name
        if alt.exists():
            return alt.resolve()
    return direct.resolve()


def oss_key(local: Path, imgs_dir: Path | None) -> str:
    if imgs_dir is not None:
        try:
            return local.resolve().relative_to(imgs_dir.resolve()).as_posix()
        except ValueError:
            pass
    return local.name


def content_type(p: Path) -> str:
    return {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
    }.get(p.suffix.lower(), "application/octet-stream")


def scan_images(files: list[Path]) -> list[dict]:
    items: list[dict] = []
    for md in files:
        try:
            text = md.read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        raws = {m.group(1).strip() for m in MD_IMG.finditer(text)}
        raws |= {m.group(1).strip() for m in HTML_IMG.finditer(text)}
        for raw in sorted(raws):
            if not raw or is_remote(raw):
                continue
            resolved = resolve_image(md, raw)
            items.append({
                "md": str(md),
                "raw": raw,
                "path": str(resolved),
                "exists": resolved.exists(),
                "imgs_dir": str(find_imgs_dir(md) or ""),
                "status": "LOCAL",
            })
    return items


def cmd_images_scan(args) -> int:
    files = iter_md(args.paths)
    items = scan_images(files)
    missing = [i for i in items if not i["exists"]]
    print(f"扫描 {len(files)} 个文件，本地图片引用 {len(items)} 处")
    for i in items:
        flag = "OK   " if i["exists"] else "缺失 "
        print(f"  [{flag}] {i['raw']}\n           → {i['path']}")
    if args.json:
        print(json.dumps({"files": len(files), "refs": len(items),
                          "missing": len(missing), "items": items},
                         ensure_ascii=False, indent=2))
    return 0


def rewrite_refs(items: list[dict]) -> tuple[int, int]:
    by_md: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        if it.get("status") in ("UPLOADED", "EXIST") and it.get("key"):
            by_md[it["md"]].append(it)

    replaced = 0
    changed_files = 0
    for md_str, refs in by_md.items():
        md = Path(md_str)
        text = md.read_text("utf-8")
        new = text
        for it in refs:
            url = OSS_BASE + quote(it["key"], safe="/-_.~")
            if it["raw"] in new:
                new = new.replace(it["raw"], url)
                replaced += 1
        if new != text:
            bak = md.with_name(md.name + ".bak")
            if not bak.exists():
                shutil.copy2(md, bak)
            md.write_text(new, "utf-8")
            changed_files += 1
    return replaced, changed_files


def cmd_images_upload(args) -> int:
    files = iter_md(args.paths)
    items = scan_images(files)
    if not items:
        print("未发现本地图片引用，无需上传")
        return 0

    missing = [i for i in items if not i["exists"]]
    apply_changes = bool(args.apply and not args.dry_run)
    if apply_changes and missing and not args.skip_missing:
        print(f"有 {len(missing)} 处图片文件不存在，已中止（可用 --skip-missing 跳过）：")
        for i in missing[:50]:
            print(f"  [缺失] {i['raw']}  ← {i['md']}")
        return die("请先补齐缺失图片，或加 --skip-missing 继续")

    ak = os.environ.get("OSS_ACCESS_KEY_ID", "").strip()
    sk = os.environ.get("OSS_ACCESS_KEY_SECRET", "").strip()
    if not ak or not sk:
        return die("未设置 OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET"
                   "（不要从 config.json 或 docs/AccessKey.csv 读取密钥）")
    try:
        import oss2
    except ImportError:
        return die("缺少 oss2：pip install oss2")

    bucket = oss2.Bucket(oss2.Auth(ak, sk), OSS_ENDPOINT, OSS_BUCKET)
    groups: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        groups[it["path"]].append(it)

    stats = defaultdict(int)
    print(f"共 {len(groups)} 张唯一图片，{len(items)} 处引用"
          f"{'（实际执行）' if apply_changes else '（预览，不修改文件）'}")

    for path_str, refs in sorted(groups.items()):
        local = Path(path_str)
        imgs_dir = Path(refs[0]["imgs_dir"]) if refs[0]["imgs_dir"] else None
        key = oss_key(local, imgs_dir)
        if not local.exists():
            stats["missing"] += 1
            for r in refs:
                r["status"] = "MISSING"
            print(f"  [缺失]   {key}")
            continue

        exists_same = False
        try:
            meta = bucket.head_object(OSS_KEY_PREFIX + key)
            exists_same = int(meta.content_length) == local.stat().st_size
        except Exception:
            exists_same = False

        if exists_same and not args.force:
            stats["existed"] += 1
            for r in refs:
                r.update(status="EXIST", key=key)
            print(f"  [已存在] {key}")
            continue

        if not apply_changes:
            stats["would_upload"] += 1
            for r in refs:
                r.update(status="WOULD_UPLOAD", key=key)
            print(f"  [待上传] {key}")
            continue

        ok = False
        for attempt in range(3):
            try:
                bucket.put_object_from_file(
                    OSS_KEY_PREFIX + key, str(local),
                    headers={"Content-Type": content_type(local)},
                )
                ok = True
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    print(f"  [失败]   {key}: {exc}")
                time.sleep(2 ** attempt)
        if ok:
            stats["uploaded"] += 1
            for r in refs:
                r.update(status="UPLOADED", key=key)
            print(f"  [上传]   {key}")
        else:
            stats["failed"] += 1
            for r in refs:
                r["status"] = "FAILED"

    replaced = changed = 0
    if apply_changes:
        replaced, changed = rewrite_refs(items)

    print(
        f"完成：上传 {stats['uploaded']}，已存在 {stats['existed']}，"
        f"待上传 {stats['would_upload']}，缺失 {stats['missing']}，失败 {stats['failed']}；"
        f"替换 {replaced} 处 / {changed} 个文件"
    )
    if args.json:
        print(json.dumps({
            "applied": apply_changes,
            "uploaded": stats["uploaded"], "existed": stats["existed"],
            "would_upload": stats["would_upload"], "missing": stats["missing"],
            "failed": stats["failed"], "replaced": replaced,
            "changed_files": changed,
            "items": items,
        }, ensure_ascii=False, indent=2))
    return 1 if stats["failed"] else 0


# ── build ──────────────────────────────────────────────────


def stage_single(md: Path, root: Path) -> Path:
    stage_root = root / "build" / "stage"
    stage_root.mkdir(parents=True, exist_ok=True)
    d = Path(tempfile.mkdtemp(dir=str(stage_root), prefix="one_"))
    shutil.copy2(md, d / md.name)
    src = md.parent / "imgs"
    if src.is_dir():
        try:
            (d / "imgs").symlink_to(src, target_is_directory=True)
        except OSError:
            pass
    return d


def collect_chapters(paths, published_only: bool, root: Path):
    chapters: list[tuple[str, str]] = []
    excluded: list[tuple[Path, str]] = []
    staged: list[Path] = []
    chapter_files: list[list[Path]] = []

    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_file():
            if p.suffix.lower() not in (".md", ".markdown"):
                continue
            if published_only and not is_published(p):
                excluded.append((p, exclude_reason(p)))
                continue
            stage = stage_single(p, root)
            staged.append(stage)
            chapters.append((str(stage), p.stem))
            chapter_files.append([p])
            continue

        if not p.is_dir():
            print(f"[跳过] 路径不存在: {p}")
            continue

        groups: list[tuple[Path, list[Path]]] = []
        top = [f for f in sorted(p.glob("*.md")) if f.name != "目录.md"]
        if top:
            groups.append((p, top))
        for d in sorted((x for x in p.iterdir() if x.is_dir()), key=lambda x: natural_key(x.name)):
            if any(part in SKIP_DIRS for part in d.parts):
                continue
            sub = [f for f in sorted(d.glob("*.md")) if f.name != "目录.md"]
            if sub:
                groups.append((d, sub))

        for d, files in groups:
            kept = [f for f in files if is_published(f)] if published_only else files
            excluded.extend((f, exclude_reason(f)) for f in files if f not in kept)
            if kept:
                chapters.append((str(d), chapter_label(d.name)))
                chapter_files.append(kept)

    return chapters, excluded, staged, chapter_files


def install_selector(core, selector) -> None:
    """在 core 读取文件列表后追加一层筛选（不改源码）。"""
    original = core._collect_md_files

    def wrapped(folder, single_chapter):
        return [f for f in original(folder, single_chapter)
                if selector(os.path.join(folder, f))]

    core._collect_md_files = wrapped


def install_layout(core, page_break: str = "article") -> None:
    """版式：章为一级标题，文章降为二级；章内篇与篇之间分页（不改源码）。

    page_break:
      article — 章内每篇文章另起一页（默认）；章首第一篇紧跟章标题
      chapter — 章内文章接排
      none    — 不分页
    """
    state = {"n": 0}
    BREAK = "\n\n\\clearpage\n\n"

    def merge_folder_content(folder, dl_dir, *, single_chapter, on_log=None):
        files = core._collect_md_files(folder, single_chapter)
        parts: list[str] = []
        started_here = False
        for fname in files:
            path = os.path.join(folder, fname)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            m = TITLE_RE.search(text)
            title = m.group(1) if m else os.path.splitext(fname)[0]
            text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)
            text = core._preprocess_md(text, folder, dl_dir, on_log)

            # 章首第一篇贴着章标题排；章内后续篇另起一页
            sep = BREAK if (page_break == "article" and started_here) else ""
            started_here = True

            if single_chapter:
                parts.append(f"{sep}\n\n{text}\n")
            else:
                state["n"] += 1
                # <!--art--> 标记文章标题，供分页/居中处理时与正文小标题区分
                parts.append(f"{sep}\n\n## <!--art-->{title}\n\n{text}\n")
        return "".join(parts), len(files)

    core._merge_folder_content = merge_folder_content


_TEX_ESCAPE = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _tex_escape(text: str) -> str:
    return "".join(_TEX_ESCAPE.get(ch, ch) for ch in text)


def chapter_opening(title: str) -> list[str]:
    """章首页：标题垂直居中、字号加大，下方一条横线，前后各分页。"""
    t = _tex_escape(title)
    return [
        "\\clearpage",
        "",
        "\\phantomsection",
        "\\addcontentsline{toc}{section}{" + t + "}",
        "\\vspace*{\\fill}",
        "\\begin{center}",
        "{\\fontsize{26}{34}\\selectfont\\bfseries " + t + "}",
        "\\end{center}",
        "\\vspace{8mm}",
        "\\begin{center}",
        "\\rule{0.42\\textwidth}{0.8pt}",
        "\\end{center}",
        "\\vspace*{\\fill}",
        "\\clearpage",
        "",
    ]


ARTICLE_MARK = "<!--art-->"

# 图片默认只缩不放：超出版心宽/高的图等比缩小，避免溢出压住正文与标题
GRAPHIC_LIMIT = "\\setkeys{Gin}{max width=\\linewidth,max height=0.85\\textheight}"


def centered_subheading(title: str, article: bool = False) -> list[str]:
    """二级标题居中排：文章标题用 Large 号，正文小标题用 large 号。"""
    size = "\\Large" if article else "\\large"
    t = _tex_escape(title)
    return [
        "",
        "\\begin{center}",
        "{" + size + "\\bfseries " + t + "}",
        "\\end{center}",
        "",
    ]


def install_graphic_limit(core) -> None:
    """让 graphicx 接受 max width / max height：只在图片超出时缩小，不放大小图。

    pandoc 的导言区拿不到，所以在生成的 .tex 里往 \\begin{document} 前插
    \\usepackage[export]{adjustbox}，它给 \\includegraphics 增加这两个键。
    """
    original = core._fix_latex

    def wrapped(tex):
        tex = original(tex)
        pre = ""
        if "adjustbox" not in tex:
            pre += "\\usepackage[export]{adjustbox}\n"
        if "\\contentsname" not in tex:
            pre += "\\renewcommand{\\contentsname}{目录}\n"
        if pre and "\\begin{document}" in tex:
            tex = tex.replace("\\begin{document}", pre + "\\begin{document}", 1)
        return tex

    core._fix_latex = wrapped


def install_chapter_breaks(core, enabled: bool = True) -> None:
    """让每个章标题独占一页。

    底层把章标题拼在正文之前，包装层拿不到拼接点，所以在编译前改写 merged.md：
    除书名（第一个一级标题）外，章标题整行换成一张「章首页」——标题垂直居中、
    字号加大、下方一条横线，前后各分页，该章正文从下一页开始。
    目录条目用 addcontentsline 补回，页码指向章首页。代码块内的 # 注释跳过。
    """
    if not enabled:
        return

    original = core._compile_merged_md

    def wrapped(md_path, output_pdf, title, work, merged_count, on_log=None):
        try:
            with open(md_path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except OSError:
            return original(md_path, output_pdf, title, work, merged_count, on_log)

        out: list[str] = []
        in_fence = False
        seen_title = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
            elif not in_fence and line.startswith("# "):
                # 第一个一级标题是书名，已由 \maketitle 打印，不再生成 \section
                if seen_title:
                    out.extend(chapter_opening(line[2:].strip()))
                seen_title = True
                continue
            elif not in_fence and line.startswith("## "):
                raw = line[3:].strip()
                is_article = raw.startswith(ARTICLE_MARK)
                if is_article:
                    raw = raw[len(ARTICLE_MARK):].strip()
                out.extend(centered_subheading(raw, is_article))
                continue
            out.append(line)

        out = [GRAPHIC_LIMIT, ""] + out
        try:
            with open(md_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(out))
        except OSError:
            pass
        return original(md_path, output_pdf, title, work, merged_count, on_log)

    core._compile_merged_md = wrapped


def resolve_published_only(args) -> bool:
    """默认只收「日期前缀 + frontmatter」的成稿；只有显式 --all / published_only=False 才放开。"""
    if getattr(args, "all", False):
        return False
    if getattr(args, "published_only", None) is False:
        return False
    return True


# ── 目录（markdown）─────────────────────────────────────────


def _article_title(path: Path) -> str:
    try:
        head = path.read_text("utf-8")[:8192]
    except (OSError, UnicodeDecodeError):
        return path.stem
    m = TITLE_RE.search(head)
    return m.group(1) if m else path.stem


def render_toc(chapters, chapter_files, book_title: str) -> tuple[str, int]:
    """按现有成稿文章渲染章节表格目录（与仓库里 目录.md 的格式一致）。"""
    lines = [f"# {book_title} — 目录", ""]
    total = 0
    for (folder, _label), files in zip(chapters, chapter_files):
        name = Path(folder).name
        heading = re.sub(r"^(\d+)\.\s*", r"\1. ", name)
        lines += [f"## {heading}", "", "| 日期 | 文章 |", "|:---|:---|"]
        for f in files:
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$", f.name)
            if not m:
                continue
            total += 1
            lines.append(f"| {m.group(1)} | [{_article_title(f)}]({f.name}) |")
        lines.append("")
    lines += [
        "---",
        "",
        f"> 共 **{total}** 篇带日期前缀的文章，按章节分组排列。不含暂存/草稿/无日期文章。",
        "",
    ]
    return "\n".join(lines), total


def _existing_book_title(target: Path) -> str | None:
    """沿用已有 目录.md 的首行书名，避免每次重写变样。"""
    try:
        first = target.read_text("utf-8").split("\n", 1)[0]
    except (OSError, UnicodeDecodeError):
        return None
    m = re.match(r"^#\s+(.+?)\s+—\s+目录\s*$", first)
    return m.group(1) if m else None


def default_toc_path(paths) -> Path | None:
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if not p.is_dir():
            continue
        pref = p / "0.前言" / "目录.md"
        if pref.exists():
            return pref
        return p / "目录.md"
    return None


def sync_toc(paths, published_only: bool, root: Path, title: str | None = None) -> Path | None:
    """打包后刷新已有 目录.md；文件不存在时不动（避免意外创建）。"""
    target = default_toc_path(paths)
    if target is None or not target.exists():
        return None
    chapters, _excluded, _staged, chapter_files = collect_chapters(paths, published_only, root)
    if not chapters:
        return None
    book = title or _existing_book_title(target) or Path(paths[0]).expanduser().resolve().name
    text, _total = render_toc(chapters, chapter_files, book)
    try:
        if target.read_text("utf-8") == text:
            return target
    except OSError:
        pass
    target.write_text(text, encoding="utf-8")
    return target


def cmd_toc(args) -> int:
    root = load_packpdf()
    published_only = resolve_published_only(args)
    chapters, _excluded, _staged, chapter_files = collect_chapters(args.paths, published_only, root)
    if not chapters:
        return die("没有可写入目录的章节。")

    if getattr(args, "output", None):
        out = Path(args.output).expanduser().resolve()
    else:
        out = default_toc_path(args.paths)
    if out is None:
        return die("无法确定目录输出位置，用 -o 指定。")

    book = (getattr(args, "title", None) or _existing_book_title(out)
            or Path(args.paths[0]).expanduser().resolve().name)
    text, total = render_toc(chapters, chapter_files, book)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"目录: {out}")
    print(f"章节 {len(chapters)} 个 / 文章 {total} 篇")
    if getattr(args, "json", False):
        print(json.dumps({"toc": str(out), "chapters": len(chapters), "articles": total},
                         ensure_ascii=False, indent=2))
    return 0


def cmd_build(args) -> int:
    root = load_packpdf()
    published_only = resolve_published_only(args)

    chapters, excluded, staged, _chapter_files = collect_chapters(args.paths, published_only, root)

    print(f"章节 {len(chapters)} 个" + ("（仅已成稿文章）" if published_only else "（全部 .md）"))
    for path, label in chapters:
        print(f"  · {label}  ← {path}")
    if excluded:
        print(f"排除 {len(excluded)} 个文件：")
        for f, reason in excluded[: args.max_issues]:
            print(f"  - {f.name}（{reason}）")
        if len(excluded) > args.max_issues:
            print(f"  ... 其余 {len(excluded) - args.max_issues} 个省略")

    if args.list_only:
        if args.json:
            print(json.dumps({
                "published_only": published_only,
                "chapters": [{"label": l, "path": p} for p, l in chapters],
                "excluded": [{"file": str(f), "reason": r} for f, r in excluded],
            }, ensure_ascii=False, indent=2))
        return 0

    if not chapters:
        return die("没有可打包的章节。检查路径，或去掉 --published-only。")

    from packpdf import core
    from packpdf.deps import check_deps, ensure_toolchain_path

    ensure_toolchain_path()
    missing = [name for name, st in check_deps().items() if not st.found]
    if missing:
        return die(f"缺少依赖: {', '.join(missing)}（先运行 doctor，见 references/env-setup.md）")

    os.environ["PACKPDF_CJK_FONT"] = args.font or os.environ.get("PACKPDF_CJK_FONT") or default_font()

    if published_only:
        install_selector(core, is_published)
    page_break = getattr(args, "page_break", "article")
    install_layout(core, page_break)
    install_graphic_limit(core)
    install_chapter_breaks(core, page_break != "none")

    if args.output:
        out = Path(args.output).expanduser().resolve()
    else:
        out = root / "PDF_output" / f"{chapters[0][1] if len(chapters) == 1 else '合集'}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    title = args.title or ("合集" if len(chapters) > 1 else chapters[0][1])
    work = root / "build"
    work.mkdir(parents=True, exist_ok=True)

    print(f"标题: {title}")
    print(f"输出: {out}")
    result = core.merge_chapters_to_pdf(
        chapters, str(out), title,
        single_chapter=False,
        work_dir=str(work),
    )

    if not result.success:
        print(result.error, file=sys.stderr)
        if staged:
            print(f"暂存目录保留用于排查: {', '.join(str(s) for s in staged)}")
        print(f"编译日志: {work / 'merged.log'}")
        return 1

    for s in staged:
        shutil.rmtree(s, ignore_errors=True)

    print(f"成功: {result.output_pdf}（{result.pages} 页，{result.size_kb:.1f} KB）")

    if not getattr(args, "no_toc", False):
        # 目录书名不跟 PDF 的 --title 走，沿用 目录.md 已有首行
        refreshed = sync_toc(args.paths, published_only, root, None)
        if refreshed:
            print(f"目录已按现有文章更新: {refreshed}")

    if args.json:
        print(json.dumps({
            "success": True, "output": result.output_pdf,
            "pages": result.pages, "size_kb": result.size_kb,
            "chapters": len(chapters), "published_only": published_only,
        }, ensure_ascii=False, indent=2))
    return 0


# ── verify ─────────────────────────────────────────────────


def cmd_verify(args) -> int:
    p = Path(args.pdf).expanduser().resolve()
    if not p.exists():
        return die(f"文件不存在: {p}")

    size = p.stat().st_size
    tail = p.open("rb").read()[-4096:]
    has_eof = b"%%EOF" in tail
    pages = None
    try:
        from PyPDF2 import PdfReader
        pages = len(PdfReader(str(p)).pages)
    except Exception:  # noqa: BLE001
        pass

    ok = size > 10000 and has_eof and (pages is None or pages > 0)
    print(f"路径: {p}")
    print(f"大小: {size / 1024:.1f} KB")
    print(f"页数: {pages if pages is not None else '未知（未安装 PyPDF2）'}")
    print(f"结束标记: {'OK' if has_eof else '缺失 %%EOF'}")
    print(f"结论: {'通过' if ok else '可疑，请检查 build/merged.log'}")
    if args.json:
        print(json.dumps({"ok": ok, "pdf": str(p), "size": size,
                          "pages": pages, "eof": has_eof},
                         ensure_ascii=False, indent=2))
    return 0 if ok else 1


# ── CLI ────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PackPDF Skill 入口")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor", help="环境与依赖体检")
    p.add_argument("--font", help="指定中文字体")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("check", help="公式 / 引用 / 图片检查")
    p.add_argument("paths", nargs="+")
    p.add_argument("--posts", action="store_true", help="额外检查 post_url 引用")
    p.add_argument("--max-issues", type=int, default=40)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    images = sub.add_parser("images", help="图片扫描与 OSS 上传")
    isub = images.add_subparsers(dest="images_cmd", required=True)
    s = isub.add_parser("scan", help="列出本地图片引用")
    s.add_argument("paths", nargs="+")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_images_scan)
    u = isub.add_parser("upload", help="上传到 OSS 并替换路径")
    u.add_argument("paths", nargs="+")
    u.add_argument("--apply", action="store_true", help="实际执行（默认仅预览）")
    u.add_argument("--dry-run", action="store_true", help="仅预览")
    u.add_argument("--force", action="store_true", help="已存在也覆盖")
    u.add_argument("--skip-missing", action="store_true", help="缺图时继续")
    u.add_argument("--json", action="store_true")
    u.set_defaults(func=cmd_images_upload)

    p = sub.add_parser("build", help="合并编译 PDF")
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--output")
    p.add_argument("--title")
    p.add_argument("--font")
    p.add_argument("--published-only", action="store_const", const=True, default=None,
                   help="仅打包：文件名带日期前缀 且 有 frontmatter（默认已启用，保留以兼容旧命令）")
    p.add_argument("--all", action="store_true", help="打包全部 .md（关闭成稿筛选，调试用）")
    p.add_argument("--page-break", choices=["article", "chapter", "none"], default="article",
                   help="分页粒度：article=每篇另起页（默认），chapter=仅每章另起页，none=不分页")
    p.add_argument("--list-only", action="store_true", help="只列入选/排除清单")
    p.add_argument("--no-toc", action="store_true", help="打包后不刷新同目录的 目录.md")
    p.add_argument("--max-issues", type=int, default=40)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("toc", help="按现有成稿文章生成章节目录（markdown）")
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--output", help="输出文件，默认 <路径>/0.前言/目录.md")
    p.add_argument("--title", help="目录首行书名")
    p.add_argument("--all", action="store_true", help="连草稿一起列入（调试用）")
    p.add_argument("--published-only", action="store_const", const=True, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_toc)

    p = sub.add_parser("verify", help="校验生成的 PDF")
    p.add_argument("pdf")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_verify)

    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
