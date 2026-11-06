#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lore 文章 → 去 AI 味 V2 检测的适配层。

解决的问题：lieflat V2 的 detect.py 直接吃 Markdown，会把 YAML front matter
（title/date/slug/description…）当成正文参与统计：

  - 语义层候选里 16/96 条是 YAML 键值对（title:、date:、author: …）
  - 「提示语冒号」会把 title:、date: 这类键名冒号算成命中
  - description 里塞满顿号，会虚高「顿号并列≥3」
  - 密度分母被 front matter 撑大，所有「次/千字」口径失真

本脚本把 front matter 剥离、保留行号映射，再把正文交给 detect.py。
用法：
    python3 tools/lieflat_detect.py <article.md> [--json|--candidates] [...]
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path("/home/axu/.pi/agent/skills/lieflat-less-ai-tone")
if not (SKILL / "scripts" / "detect.py").exists():
    SKILL = Path("/tmp/lieflat-up")
DETECT = SKILL / "scripts" / "detect.py"

FM_RE = re.compile(r"^\s*---[ \t]*\n(.*?)\n---[ \t]*$", re.S | re.M)


def split_front_matter(text):
    """返回 (正文, 行号偏移)。偏移=被剥离的 front matter 行数。"""
    m = FM_RE.match(text)
    if not m:
        return text, 0
    # 保留一个空行占位，让后续行号仍然对得上（front matter 占 N 行 → 用 N 个空行替换）
    n = text[: m.end()].count("\n")
    body = "\n" * n + text[m.end():]
    return body.lstrip("\n"), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--candidates", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--max-hits", type=int, default=5)
    args = ap.parse_args()

    src = Path(args.file)
    text = src.read_text(encoding="utf-8")
    body, offset = split_front_matter(text)

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as f:
        f.write(body)
        tmp = Path(f.name)

    cmd = [sys.executable, str(DETECT), str(tmp)]
    if args.json:
        cmd.append("--json")
    if args.candidates:
        cmd.append("--candidates")
    if args.out:
        cmd += ["--out", args.out]
    cmd += ["--max-hits", str(args.max_hits)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout
    # 把临时文件名与行号偏移还原回原文
    out = out.replace(str(tmp), str(src)).replace(tmp.name, str(src))
    if args.out:
        p = Path(args.out)
        data = json.loads(p.read_text(encoding="utf-8"))
        for key in ("rename", "cohesion", "colon", "iso3"):
            for item in data.get(key, []) or []:
                item["line"] = item.get("line", 0) + offset
                item["file"] = str(src)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        print(out)
    tmp.unlink(missing_ok=True)
    if r.returncode != 0 and r.stderr:
        sys.stderr.write(r.stderr)


if __name__ == "__main__":
    main()
