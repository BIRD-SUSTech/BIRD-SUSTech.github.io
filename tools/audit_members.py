#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核对 data/members.json 的字段完整性：只输出摘要，不打印长文本。"""
import json
from pathlib import Path

import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "members.json"


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    members = d["members"]
    print(f"共 {len(members)} 位成员\n")
    print(f"{'slug':20s} {'group':14s} {'role_en':26s} edu pub  bio(en/zh)   res(en/zh)  photo email meta")
    problems = []
    for m in members:
        photo_ok = (ROOT / "images" / "people" / m.get("photo", "")).exists() if m.get("photo") else False
        row = (
            f"{m['slug']:20s} {m['group']:14s} {m['role_en']:26s} "
            f"{len(m['education']):>3} {len(m['publications']):>3}  "
            f"{len(m['bio_en']):>4}/{len(m['bio_zh']):<4} "
            f"{len(m['research_en']):>4}/{len(m['research_zh']):<4} "
            f"{'Y' if photo_ok else 'N':>5} {'Y' if m['email'] else '-':>5} "
            f"{m['meta_label_en']}{m['meta_value_en']}"
        )
        print(row)
        for key in ("name_en", "name_zh", "role_en", "role_zh", "bio_en", "bio_zh", "research_en", "research_zh"):
            if not m.get(key):
                problems.append(f"{m['slug']}: 缺 {key}")
        if not photo_ok:
            problems.append(f"{m['slug']}: 照片缺失 ({m.get('photo')})")
        if not m.get("education"):
            problems.append(f"{m['slug']}: 无教育经历")
    print()
    if problems:
        print("需要处理：")
        for p in problems:
            print("  -", p)
    else:
        print("字段完整，无缺失项。")


if __name__ == "__main__":
    main()
