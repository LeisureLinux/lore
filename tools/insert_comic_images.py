#!/usr/bin/env python3
"""把 F/OSS Comics 漫画配图插入译文 article.md。

用法：python3 insert_comic_images.py <article目录> <映射JSON>

映射 JSON 形如：[["锚点文本(段落片段)", "images/xxx.png"], ...]
脚本会在**首个**包含锚点文本的段落之后插入 markdown 图片语法。
"""
import json
import re
import sys
from pathlib import Path

MD_IMG = re.compile(r'^!\[(.*?)\]\(([^)\s]+)(?:\s+"[^"]*")?\)\s*$')


def main():
    art_dir = Path(sys.argv[1])
    pairs = json.load(open(sys.argv[2], encoding='utf-8'))
    pairs = [[a, i if i.startswith('images/') else 'images/' + i] for a, i in pairs]
    md_path = art_dir / "article.md"
    lines = md_path.read_text(encoding='utf-8').split("\n")

    existing = {m.group(2) for l in lines if (m := MD_IMG.match(l.strip()))}

    out = []
    pending = list(pairs)
    used = set()

    for line in lines:
        out.append(line)
        rest = []
        for anchor, img in pending:
            if img in existing or img in used:
                continue
            if anchor in line:
                rest.append((anchor, img))
        for anchor, img in rest:
            pending.remove([anchor, img])
            used.add(img)
            out.append("")
            out.append(f"![漫画配图：{Path(img).stem}]({img})")
            out.append("")

    md_path.write_text("\n".join(out), encoding='utf-8')
    print(f"✅ {art_dir.name}: 插入 {len(used)} 张；未匹配 {len(pending)}")
    for a, i in pending:
        print(f"   ⚠️ 未匹配：{i}  ← {a[:50]}")


if __name__ == "__main__":
    main()
