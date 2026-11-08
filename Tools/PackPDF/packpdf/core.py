"""Markdown 目录 → 合并 PDF 的核心逻辑。"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .deps import deps_ok, ensure_toolchain_path

LogFn = Callable[[str], None]
_dl_cache: dict[str, str] = {}


def _cjk_font() -> str:
    """中文字体：优先 PACKPDF_CJK_FONT，其次按平台选择。"""
    font = os.environ.get('PACKPDF_CJK_FONT', '').strip()
    if font:
        return font
    if sys.platform == 'darwin':
        return 'Songti SC'
    if sys.platform.startswith('linux'):
        return 'Noto Serif CJK SC'
    return 'SimSun'


def _mono_font() -> str:
    """代码块西文字体。

    不能用 Latin Modern Mono：它没有希腊字母，代码里的 π、α 等会被静默丢弃，
    `k * π / 2` 会渲染成 `k * /2`，语义直接坏掉。
    """
    font = os.environ.get('PACKPDF_MONO_FONT', '').strip()
    if font:
        return font
    if sys.platform == 'darwin':
        return 'Menlo'
    if sys.platform.startswith('linux'):
        return 'DejaVu Sans Mono'
    return 'Consolas'


@dataclass
class MergeResult:
    success: bool
    output_pdf: str
    pages: int | str | None = None
    size_kb: float | None = None
    merged_count: int = 0
    work_dir: str = ''
    error: str = ''


def _log(msg: str, on_log: LogFn | None) -> None:
    if on_log:
        on_log(msg)
    else:
        print(msg)


def _install_output_pdf(
    pdf_src: str,
    output_pdf: str,
    on_log: LogFn | None,
) -> tuple[bool, str, str]:
    """将编译好的 PDF 写入输出路径；若目标被占用则尝试带时间戳的备用文件名。"""
    os.makedirs(os.path.dirname(output_pdf) or '.', exist_ok=True)

    def _copy(dst: str) -> None:
        shutil.copy(pdf_src, dst)

    try:
        _copy(output_pdf)
        return True, output_pdf, ''
    except PermissionError:
        pass
    except OSError as exc:
        if getattr(exc, 'errno', None) not in (13, None):
            return False, output_pdf, f'无法写入 PDF:\n{output_pdf}\n\n{exc}'

    base, ext = os.path.splitext(output_pdf)
    alt = f'{base}_{time.strftime("%Y%m%d_%H%M%S")}{ext}'
    try:
        _copy(alt)
        _log(
            f'[警告] 无法覆盖（文件可能正被打开）: {output_pdf}，已改存: {alt}',
            on_log,
        )
        return True, alt, ''
    except (PermissionError, OSError):
        err = (
            f'无法写入 PDF（权限被拒绝）:\n{output_pdf}\n\n'
            f'常见原因：\n'
            f'  · 该 PDF 正在阅读器中打开\n'
            f'  · OneDrive 正在同步该文件\n\n'
            f'请先关闭相关程序后重试。'
        )
        return False, output_pdf, err


def _download(url: str, dl_dir: str, on_log: LogFn | None) -> str:
    if url in _dl_cache:
        return _dl_cache[url]
    try:
        ext = os.path.splitext(url.split('?')[0])[1] or '.png'
        fname = hashlib.md5(url.encode()).hexdigest()[:12] + ext
        local = os.path.join(dl_dir, fname)
        if not os.path.exists(local):
            urllib.request.urlretrieve(url, local)

        with open(local, 'rb') as f:
            header = f.read(6)
        if header[:3] == b'GIF':
            try:
                from PIL import Image

                img = Image.open(local)
                png_local = os.path.splitext(local)[0] + '.png'
                img.save(png_local, 'PNG')
                if png_local != local:
                    os.remove(local)
                local = png_local
                _log(f'  [转换] GIF→PNG: {os.path.basename(local)}', on_log)
            except ImportError:
                _log('  [跳过] Pillow 未安装，无法转换 GIF', on_log)
                _dl_cache[url] = ''
                return ''

        _dl_cache[url] = local
        return local
    except Exception:
        _dl_cache[url] = ''
        return ''


CJK_RE = re.compile(r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+)')


def _has_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s))


def _wrap_cjk(s: str) -> str:
    return CJK_RE.sub(lambda m: r'\text{' + m.group(1) + '}', s)


def _preprocess_md(text: str, base_dir: str, dl_dir: str, on_log: LogFn | None) -> str:
    text = text.replace('{% raw %}', '').replace('{% endraw %}', '').replace('<!--more-->', '')
    text = re.sub(r'<img[^>]*/?>', '', text)

    def _resolve_img(m: re.Match[str]) -> str:
        alt, path = m.group(1), m.group(2)
        if path.startswith('http'):
            local = _download(path, dl_dir, on_log)
            return f'![{alt}]({local})' if local and os.path.exists(local) else ''
        for c in [
            os.path.normpath(os.path.join(base_dir, path)),
            os.path.normpath(os.path.join(base_dir, '..', '..', '..', path.replace('\\', '/'))),
        ]:
            if os.path.exists(c):
                return f'![{alt}]({c})'
        return ''

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _resolve_img, text)

    def _upgrade_cases_inline(m: re.Match[str]) -> str:
        full = m.group(0)
        inner = m.group(1)
        if '\\begin{cases}' in inner or '\\begin{array}' in inner:
            return '$$' + inner + '$$'
        return full

    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _upgrade_cases_inline, text)

    def _fix_math_block(m: re.Match[str]) -> str:
        inner = m.group(1)
        return '$$' + _wrap_cjk(inner) + '$$' if _has_cjk(inner) else m.group(0)

    text = re.sub(r'\$\$(.+?)\$\$', _fix_math_block, text, flags=re.DOTALL)

    def _fix_inline_math(m: re.Match[str]) -> str:
        inner = m.group(1)
        return '$' + _wrap_cjk(inner) + '$' if _has_cjk(inner) else m.group(0)

    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _fix_inline_math, text)
    return text


def _fix_latex(tex: str) -> str:
    tex = tex.replace(r'\textdollar', r'\$')
    tex = re.sub(r'\\\$\s*\n\s*\n(\s*\\begin\{cases\})', r'$\n\n\1', tex)
    tex = re.sub(r'(\\end\{cases\})\s*\n\s*\n\s*\\\$', r'\1\n\n$', tex)
    tex = re.sub(r'\\\$\s*\n\s*\n\s*\$\$', r'$$\n\n$$', tex)
    tex = re.sub(
        r'([a-zA-Z]:[^\s{}]+\.\./[^\s{}]+)',
        lambda m: os.path.normpath(m.group(1)),
        tex,
    )
    tex = tex.replace(r'\begin{figure}[htbp]', r'\begin{figure}[H]')
    if r'\usepackage{float}' not in tex:
        tex = tex.replace(
            r'\usepackage{graphicx}',
            r'\usepackage{graphicx}' + '\n' + r'\usepackage{float}',
        )
    # 代码块要同时指定中西文等宽字体：西文沿用 Latin Modern Mono 时，
    # 希腊字母（π 等）没有字形会被静默丢弃；中文不指定则退到比例宋体，
    # 与等宽西文挤在一起导致缩进和列对不齐。
    if r'\setCJKmonofont' not in tex:
        cjk = _cjk_font()
        anchor = r'\setCJKmainfont[]{%s}' % cjk
        if anchor in tex:
            tex = tex.replace(
                anchor,
                anchor + '\n'
                + r'\setCJKmonofont[]{%s}' % cjk + '\n'
                + r'\setmonofont[]{%s}' % _mono_font(),
            )
    if r'\sloppy' not in tex:
        tex = tex.replace(r'\begin{document}', r'\sloppy' + '\n' + r'\begin{document}')
    return tex


def default_work_dir(app_root: str | None = None) -> str:
    root = app_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'build')


def _collect_md_files(folder: str, single_chapter: bool) -> list[str]:
    files = sorted(f for f in os.listdir(folder) if f.endswith('.md') and f != '目录.md')
    if single_chapter:
        files = [f for f in files if not re.match(r'^0\.', f)]
    return files


def _merge_folder_content(
    folder: str,
    dl_dir: str,
    *,
    single_chapter: bool,
    on_log: LogFn | None,
) -> tuple[str, int]:
    files = _collect_md_files(folder, single_chapter)
    parts: list[str] = []
    for i, fname in enumerate(files, start=1):
        path = os.path.join(folder, fname)
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        m = re.search(r'^title:\s*[\"\']?(.+?)[\"\']?\s*$', text, re.M)
        tt = m.group(1) if m else os.path.splitext(fname)[0]
        text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, count=1, flags=re.DOTALL)
        text = _preprocess_md(text, folder, dl_dir, on_log)
        if single_chapter:
            parts.append(f'\n\n{text}\n')
        else:
            parts.append(f'\n\n# 第{i}章  {tt}\n\n{text}\n')
    return ''.join(parts), len(files)


def _compile_merged_md(
    md_path: str,
    output_pdf: str,
    title: str,
    work: str,
    merged_count: int,
    on_log: LogFn | None,
) -> MergeResult:
    output_pdf = os.path.abspath(output_pdf)
    tex_path = os.path.join(work, 'merged.tex')
    r = subprocess.run(
        [
            'pandoc', md_path, '-o', tex_path,
            '--standalone', '--toc', '--toc-depth=1',
            '-f', 'markdown+tex_math_dollars+raw_tex',
            '-V', f'mainfont={_cjk_font()}',
            '-V', f'title={title}',
            '-V', f'CJKmainfont={_cjk_font()}',
            '-V', 'geometry=margin=2.5cm',
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or '')[-800:]
        return MergeResult(
            success=False,
            output_pdf=output_pdf,
            merged_count=merged_count,
            work_dir=work,
            error=f'pandoc 转换失败:\n{err}',
        )

    with open(tex_path, 'r', encoding='utf-8') as fh:
        tex = fh.read()
    tex = _fix_latex(tex)
    with open(tex_path, 'w', encoding='utf-8') as fh:
        fh.write(tex)
    _log(f'LaTeX: {len(tex)} 字符', on_log)

    for i in range(2):
        _log(f'xelatex 第 {i + 1} 遍...', on_log)
        subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-output-directory', work, 'merged.tex'],
            capture_output=True,
            cwd=work,
            timeout=300,
            encoding='utf-8',
            errors='replace',
        )

    pdf_src = os.path.join(work, 'merged.pdf')
    if os.path.exists(pdf_src) and os.path.getsize(pdf_src) > 10000:
        with open(pdf_src, 'rb') as f:
            content = f.read()
        if content.rfind(b'%%EOF') > 0 and content.rfind(b'startxref') > 0:
            ok, final_pdf, err = _install_output_pdf(pdf_src, output_pdf, on_log)
            if not ok:
                _dl_cache.clear()
                return MergeResult(
                    success=False,
                    output_pdf=output_pdf,
                    merged_count=merged_count,
                    work_dir=work,
                    error=err,
                )
            sz = os.path.getsize(final_pdf) / 1024
            pages: int | str = '?'
            try:
                from PyPDF2 import PdfReader

                pages = len(PdfReader(final_pdf).pages)
            except Exception:
                pass
            _log(f'已生成: {final_pdf} ({sz:.1f} KB, {pages} 页)', on_log)
            _dl_cache.clear()
            return MergeResult(
                success=True,
                output_pdf=final_pdf,
                pages=pages,
                size_kb=sz,
                merged_count=merged_count,
                work_dir=work,
            )

    log_path = os.path.join(work, 'merged.log')
    err_lines: list[str] = ['PDF 不完整或编译失败。']
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8', errors='replace') as fh:
            log = fh.read()
        errs = re.findall(r'^!.*', log, re.MULTILINE)
        err_lines.append(f'xelatex 错误 ({len(errs)}):')
        err_lines.extend(f'  {e.strip()}' for e in errs[:20])
    err_lines.append(f'中间文件保留在: {work}')
    _dl_cache.clear()
    return MergeResult(
        success=False,
        output_pdf=output_pdf,
        merged_count=merged_count,
        work_dir=work,
        error='\n'.join(err_lines),
    )


def merge_chapters_to_pdf(
    chapters: list[tuple[str, str]],
    output_pdf: str,
    title: str = '合集',
    *,
    single_chapter: bool = True,
    work_dir: str | None = None,
    extra_path: list[str] | None = None,
    on_log: LogFn | None = None,
) -> MergeResult:
    """将多个章节目录合并编译为一个 PDF。chapters: [(folder_path, chapter_label), ...]"""
    output_pdf = os.path.abspath(output_pdf)
    ensure_toolchain_path(extra_path)

    if not deps_ok(extra_path):
        return MergeResult(
            success=False,
            output_pdf=output_pdf,
            error='缺少 pandoc 或 xelatex，请先安装并确保在 PATH 中可用。',
        )
    if not chapters:
        return MergeResult(success=False, output_pdf=output_pdf, error='未选择任何章节')

    work = os.path.abspath(work_dir or default_work_dir())
    os.makedirs(work, exist_ok=True)
    dl_dir = os.path.join(work, 'images')
    os.makedirs(dl_dir, exist_ok=True)

    multi = len(chapters) > 1
    merged = f'# {title}\n\n'
    total_files = 0

    for folder, chapter_label in chapters:
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            return MergeResult(
                success=False,
                output_pdf=output_pdf,
                error=f'目录不存在: {folder}',
            )
        body, count = _merge_folder_content(folder, dl_dir, single_chapter=single_chapter, on_log=on_log)
        if count == 0:
            _log(f'[跳过] {chapter_label}: 无 .md 文件', on_log)
            continue
        total_files += count
        if multi:
            merged += f'\n\n# {chapter_label}\n\n'
        merged += body
        _log(f'  章节 {chapter_label}: {count} 篇', on_log)

    if total_files == 0:
        return MergeResult(success=False, output_pdf=output_pdf, error='所选章节中均未找到 .md 文件')

    md_path = os.path.join(work, 'merged.md')
    with open(md_path, 'w', encoding='utf-8') as fh:
        fh.write(merged)
    _log(f'合并: {len(chapters)} 章 / {total_files} 篇, {len(merged)} 字符', on_log)

    return _compile_merged_md(md_path, output_pdf, title, work, total_files, on_log)


def merge_to_pdf(
    folder: str,
    output_pdf: str,
    title: str = '合集',
    *,
    single_chapter: bool = False,
    work_dir: str | None = None,
    extra_path: list[str] | None = None,
    on_log: LogFn | None = None,
) -> MergeResult:
    """将 folder 内 .md 文件合并并编译为 PDF。"""
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        return MergeResult(
            success=False,
            output_pdf=os.path.abspath(output_pdf),
            error=f'目录不存在: {folder}',
        )
    return merge_chapters_to_pdf(
        [(folder, title)],
        output_pdf,
        title,
        single_chapter=single_chapter,
        work_dir=work_dir,
        extra_path=extra_path,
        on_log=on_log,
    )
