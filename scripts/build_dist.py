#!/usr/bin/env python3
"""组装 Cloudflare Pages 的发布目录 dist/。

只复制对外提供的静态文件（各索引 YAML 与 _headers），避免把 src/、scripts/、.venv
等一并上传。发布内容：

    index.yaml
    _headers
    rimes/index.yaml
    plugins/index.yaml
    plugins/v2/index.yaml
    models/index.yaml
    layouts/index.yaml

用法：
    python scripts/build_dist.py
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")

# 需要发布的顶层条目（文件或目录，逐项复制）
PUBLISH = ["index.yaml", "_headers", "rimes", "plugins", "models", "layouts"]


def main() -> int:
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    missing = []
    count = 0
    for name in PUBLISH:
        src = os.path.join(ROOT, name)
        dst = os.path.join(DIST, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            missing.append(name)
            continue
        count += 1

    print(f"  ✓ 已组装 dist/（{count}/{len(PUBLISH)} 项）")
    for dirpath, _dirs, files in os.walk(DIST):
        for fn in sorted(files):
            rel = os.path.relpath(os.path.join(dirpath, fn), DIST)
            size = os.path.getsize(os.path.join(dirpath, fn))
            print(f"    {rel}  ({size} B)")

    if missing:
        print(f"  ⚠ 缺少以下发布项：{', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
