#!/usr/bin/env python3
"""
CI 自动补全脚本 — 直接修改源文件，不经过 build/ 目录。

用法:
  python scripts/ci-update.py               # 补全并写回源文件
  python scripts/ci-update.py --check       # 仅检查是否有缺失
"""

import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (
    ROOT, load_yaml, dump_yaml,
    fill_download_urls, fill_archive, fill_files_checksums,
    recalc_model_size,
    should_skip_version,
    enable_proxy,
)

# ─── 源码目录 vs 输出目录 ────────────────────────────────
# 源码: src/rimes/*.yaml, src/plugins/*.yaml, src/models/*.yaml
# 输出: rimes/index.yaml, plugins/index.yaml, models/index.yaml
SRC_DIR = os.path.join(ROOT, "src")
SKIP_FILES = {"index.yaml"}

# ─── 字段白名单（同 generate_index.py）───────────────────

SCHEMA_FIELDS = [
    "id", "name", "author", "description", "type",
    "tags", "homepage", "license", "dependencies",
    "appVersion", "warning", "currentVersion", "versions",
]
PLUGIN_FIELDS = [
    "id", "name", "author", "description", "type",
    "tags", "pluginType", "homepage", "license",
    "appVersion", "warning", "currentVersion", "versions",
]
MODEL_FIELDS = [
    "id", "name", "author", "description", "category", "size",
    "type", "tags", "homepage", "license", "appVersion", "warning",
    "currentVersion", "versions",
]


# ─── 检查是否有缺失 ──────────────────────────────────────


def check():
    any_needed = False
    for subdir in ("rimes", "plugins", "models"):
        src_dir = os.path.join(SRC_DIR, subdir)
        for fpath in sorted(glob.glob(os.path.join(src_dir, "*.yaml"))):
            basename = os.path.basename(fpath)
            data = load_yaml(fpath)
            if not data:
                continue
            eid = data.get("id", "?")
            for v in data.get("versions", []):
                ver = v.get("version", "?")
                if should_skip_version(ver):
                    continue
                for dl in v.get("downloadUrl", []):
                    url = dl.get("url", "")
                    if url and (not dl.get("sha256") or not dl.get("size")):
                        if url.endswith(".gram"):
                            continue  # .gram 文件不检查 sha256
                        print(f"  ⚠ src/{subdir}/{basename} ({eid} v{ver}): 缺 sha256/size")
                        any_needed = True
                if "archive" in v:
                    a = v["archive"]
                    if a.get("url") and (not a.get("sha256") or not a.get("size")):
                        print(f"  ⚠ src/{subdir}/{basename} ({eid} v{ver} archive): 缺 sha256/size")
                        any_needed = True
                for fi, f_item in enumerate(v.get("files", [])):
                    if f_item.get("url") and (not f_item.get("sha256") or not f_item.get("size")):
                        print(f"  ⚠ src/{subdir}/{basename} ({eid} v{ver} files[{fi}]): 缺 sha256/size")
                        any_needed = True
    if any_needed:
        sys.exit(1)


# ─── 补合并写回源文件 ──────────────────────────────────


def update_source(subdir: str, fields: list, filler):
    """处理单个子目录：从 src/ 读源码 → 补全 checksum → 输出 index.yaml（不修改 src/）"""
    from datetime import date
    today = date.today().isoformat()

    src_dir = os.path.join(SRC_DIR, subdir)
    out_dir = os.path.join(ROOT, subdir)

    entries = []
    for fpath in sorted(glob.glob(os.path.join(src_dir, "*.yaml"))):
        basename = os.path.basename(fpath)
        data = load_yaml(fpath)
        if not data:
            continue
        eid = os.path.splitext(basename)[0]
        if data.get("id") != eid:
            print(f"  ⚠ {basename}: id 不匹配，跳过")
            continue

        print(f"  📄 src/{subdir}/{basename}")
        filled = filler({f: enable_proxy(data[f]) if f == "versions"
                         else data[f] for f in data})  # 只补全内存数据，不写回 src/
        entry = {f: filled[f] for f in fields if f in filled and filled[f] is not None}
        entries.append(entry)

    # type: built-in 优先排在前面，其余按 id 排序
    entries.sort(
        key=lambda e: (
            e.get("type") != "built-in",
            e.get("id", ""),
        )
    )

    # 输出 index.yaml 到根级目录（rimes/ plugins/ models/）
    HEADERS = {
        "rimes": "# Xime 输入方案子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
        "plugins": "# Xime 插件子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
        "models": "# Xime 模型子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
    }
    key_map = {"rimes": "schemas", "plugins": "plugins", "models": "models"}
    key = key_map[subdir]

    os.makedirs(out_dir, exist_ok=True)
    index = {"index_version": 1, "updated_at": today, key: entries}
    yaml_str = yaml.dump(index, allow_unicode=True, default_flow_style=False, sort_keys=False)
    index_path = os.path.join(out_dir, "index.yaml")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(HEADERS[subdir] + yaml_str)
    print(f"  ✓ 已重新生成 {subdir}/index.yaml ({len(entries)} 条目)")


def update():
    print("=" * 50)
    print("🔄 CI 自动补全 sha256/size/sizeBytes")
    print("=" * 50)

    update_source("rimes", SCHEMA_FIELDS, fill_download_urls)
    print()
    update_source("plugins", PLUGIN_FIELDS, fill_download_urls)
    print()
    update_source("models", MODEL_FIELDS, lambda d: recalc_model_size(fill_files_checksums(fill_archive(d))))

    print(f"\n{'=' * 50}")
    print("✅ 所有源文件已更新")
    print(f"{'=' * 50}")


def main():
    if "--check" in sys.argv:
        check()
    else:
        update()


if __name__ == "__main__":
    main()
