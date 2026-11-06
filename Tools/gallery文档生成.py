#!/usr/bin/env python3
"""Gallery Pipeline: 将 gallery/*.md 转为 HTML 存入 _data/gallery_help.yml

用法：
    python Tools/gallery_pipeline.py

每次修改 gallery 下的 .md 说明文档后运行此脚本，
Jekyll 构建时会自动读取 _data/gallery_help.yml 渲染帮助面板。
"""

import os
import re
import yaml
from pathlib import Path
import html

try:
    import markdown as md_lib
except ImportError:
    print("错误：需要安装 markdown 库，请运行: pip install markdown")
    import sys
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = ROOT / 'gallery'
OUTPUT_FILE = ROOT / '_data' / 'gallery_help.yml'


def slugify(filename: str) -> str:
    """WebGL Water.md → webgl-water"""
    name = Path(filename).stem
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.strip().lower()).strip('-')
    return slug


def convert_md_to_html(md_content: str) -> str:
    """将 Markdown 转为 HTML，保留数学公式和特殊格式"""
    extensions = [
        'tables',
        'fenced_code',
        'codehilite',
        'nl2br',
    ]
    # 使用 markdown 库将 MD 转为 HTML
    html_content = md_lib.markdown(md_content, extensions=extensions)

    # 处理注释掉的图片 (<!-- ... -->)，markdown 不会渲染它们
    # 直接保留 HTML 注释

    return html_content


def main():
    if not GALLERY_DIR.exists():
        print(f"错误：gallery 目录不存在: {GALLERY_DIR}")
        return

    help_data = {}

    md_files = sorted(GALLERY_DIR.glob('*.md'))
    # 跳过 README 等非说明文档
    md_files = [f for f in md_files if not f.name.upper().startswith('README')]
    if not md_files:
        print("警告：gallery 目录下没有 .md 文件")
        return

    for md_file in md_files:
        slug = slugify(md_file.name)
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 处理 Jekyll frontmatter（如果 md 有的话，去掉它）
        if md_content.startswith('---'):
            parts = md_content.split('---', 2)
            if len(parts) >= 3:
                md_content = parts[2].strip()

        html_content = convert_md_to_html(md_content)
        help_data[slug] = html_content
        print(f"  ✓ {md_file.name} → slug: {slug} ({len(html_content)} chars)")

    # 写入 YAML
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(
            help_data, f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=1000  # 避免长行被截断
        )

    print(f"\n✓ 已生成 {OUTPUT_FILE}，包含 {len(help_data)} 个条目")


if __name__ == '__main__':
    main()
