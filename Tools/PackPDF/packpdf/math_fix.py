"""批量修复 Markdown 公式规范问题。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .preprocess import wrap_chinese_in_math


@dataclass
class MathFixResult:
    scanned: int = 0
    fixed_files: int = 0
    unchanged_files: int = 0
    details: list[tuple[str, list[str]]] = field(default_factory=list)
    error: str = ''


def _replace_norm_pipes(text: str) -> tuple[str, bool]:
    """将 \\|...\\| 范数替换为 \\lVert...\\rVert，平衡配对。

    代码块里的 `\\|` 往往是 ASCII 作图（网格示意图之类），不是范数，跳过不动。
    """
    expect_open = True
    changed = False
    in_fence = False
    out_lines: list[str] = []
    for line in text.split('\n'):
        if line.lstrip().startswith(('```', '~~~')):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence or '\\|' not in line:
            out_lines.append(line)
            continue
        buf: list[str] = []
        i = 0
        while i < len(line):
            if line[i:i+2] == '\\|':
                if expect_open:
                    buf.append('\\lVert ')
                    expect_open = False
                else:
                    buf.append('\\rVert ')
                    expect_open = True
                changed = True
                i += 2
            else:
                buf.append(line[i])
                i += 1
        out_lines.append(''.join(buf))
    return '\n'.join(out_lines), changed


def _fix_inline_display(text: str) -> tuple[str, bool]:
    """把夹在句子中间的 $$...$$ 降级为行内 $...$。

    块级公式会独占一行居中，写在句子里会把整段话切碎。
    整行只有 $$、或 $$...$$ 独占一行的才是真块级，保持不动。
    """
    out: list[str] = []
    changed = False
    in_fence = False

    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or '$$' not in line:
            out.append(line)
            continue

        stripped = line.strip()
        if not stripped or stripped == '$$':
            out.append(line)
            continue

        positions = [m.start() for m in re.finditer(r'\$\$', line)]
        if len(positions) % 2:  # 交给 dollar_pair 规则处理
            out.append(line)
            continue

        lead = len(line) - len(line.lstrip())
        trail = len(line.rstrip())
        if positions[0] > lead or positions[-1] + 2 < trail:
            out.append(line.replace('$$', '$'))
            changed = True
        else:
            out.append(line)

    return '\n'.join(out), changed


def fix_text(text: str) -> tuple[str, list[str]]:
    """返回 (修复后文本, 变更说明列表)。"""
    changes: list[str] = []

    text, inline_changed = _fix_inline_display(text)
    if inline_changed:
        changes.append('句中 $$ 降级为行内 $')

    double_fixed = re.sub(r'\\\(\$([^$]*)\$\\\)', r'$\1$', text)
    if double_fixed != text:
        changes.append('移除 \\(\\) 与 $ 双重包裹')
        text = double_fixed

    norm_fixed, norm_changed = _replace_norm_pipes(text)
    if norm_changed:
        changes.append('\\| 范数改为 \\lVert / \\rVert')
        text = norm_fixed

    segments = re.split(r'(\$\$.+?\$\$)', text, flags=re.DOTALL)

    for i, seg in enumerate(segments):
        if seg.startswith('$$') and seg.endswith('$$'):
            body = seg[2:-2]
            new_body = re.sub(r'\n\s*\n', '\n', body)
            if new_body != body:
                changes.append('$$ 块内删除空行')
                body = new_body
            sub_fixed = re.sub(
                r'\\sub(?=\s|\{|\[)(?!section|stack|set)',
                r'\\subset',
                body,
            )
            if sub_fixed != body:
                changes.append('\\sub 改为 \\subset')
                body = sub_fixed
            wrapped = wrap_chinese_in_math(body)
            if wrapped != body:
                changes.append('块公式中文包裹 \\text{}')
                body = wrapped
            segments[i] = '$$' + body + '$$'
        else:
            seg = segments[i]

            def _fix_inline(m: re.Match[str]) -> str:
                body = m.group(1)
                if r'\begin{cases}' in body:
                    wrapped = wrap_chinese_in_math(body)
                    if r'\text{' in wrapped and wrapped != body:
                        changes.append('行内 cases 改为独立 $$ 块；中文包裹 \\text{}')
                    else:
                        changes.append('行内 cases 改为独立 $$ 块')
                    return '\n$$' + wrapped + '$$\n'
                wrapped = wrap_chinese_in_math(body)
                if wrapped != body:
                    changes.append('行内公式中文包裹 \\text{}')
                return '$' + wrapped + '$'

            seg = re.sub(
                r'(?<!\$)\$(?!\$)((?:[^$]|\\\$)+?)\$(?!\$)',
                _fix_inline,
                seg,
            )
            spaced = re.sub(r'([\u4e00-\u9fff])\$(?!\$)', r'\1 $', seg)
            spaced = re.sub(r'(?<!\$)\$(?!\$)([\u4e00-\u9fff])', r'$ \1', spaced)
            if spaced != seg:
                changes.append('$ 前后补充空格')
                seg = spaced
            segments[i] = seg

    text = ''.join(segments)
    return text, list(dict.fromkeys(changes))


def fix_file(filepath: str | Path) -> tuple[bool, list[str]]:
    path = Path(filepath)
    original = path.read_text(encoding='utf-8')
    new_text, changes = fix_text(original)
    if new_text != original:
        path.write_text(new_text, encoding='utf-8')
        return True, changes
    return False, []


def fix_files(file_paths: list[str | Path]) -> MathFixResult:
    result = MathFixResult(scanned=len(file_paths))
    for raw in file_paths:
        path = Path(raw)
        if not path.is_file():
            continue
        try:
            ok, changes = fix_file(path)
        except OSError as exc:
            result.error = str(exc)
            return result
        if ok:
            result.fixed_files += 1
            result.details.append((str(path.resolve()), changes))
        else:
            result.unchanged_files += 1
    return result


def fix_directory(root: str | Path, *, recursive: bool = True) -> MathFixResult:
    root = Path(root)
    pattern = '**/*.md' if recursive else '*.md'
    paths = sorted(root.glob(pattern))
    return fix_files(paths)
