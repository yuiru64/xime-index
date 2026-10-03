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
# 源码: src/rimes/*.yaml, src/plugins/v1/*.yaml, src/plugins/v2/*.yaml, src/models/*.yaml, src/layouts/*.yaml
# 输出: rimes/index.yaml, plugins/index.yaml, plugins/v2/index.yaml, models/index.yaml, layouts/index.yaml
SRC_DIR = os.path.join(ROOT, "src")
SKIP_FILES = {"index.yaml"}

# ─── 字段白名单（同 generate_index.py）───────────────────

SCHEMA_FIELDS = [
    "id", "name", "author", "description", "type",
    "tags", "homepage", "license", "dependencies",
    "appVersion", "warning", "currentVersion", "versions",
    "recipes", "schemas",
]
PLUGIN_FIELDS = [
    "id", "name", "author", "description", "type",
    "tags", "pluginType", "homepage", "license",
    "appVersion", "warning", "currentVersion", "versions",
]
# v2 插件索引（JS/QuickJS，宿主 >=3.0.0）：在旧字段上追加新插件系统的元数据
PLUGIN_V2_FIELDS = [
    "id", "name", "author", "description", "type",
    "tags", "pluginType", "icon", "activation",
    "minHostVersion", "platforms", "capabilities", "network",
    "homepage", "license",
    "appVersion", "warning", "currentVersion", "versions",
]
MODEL_FIELDS = [
    "id", "name", "author", "description", "category", "size",
    "type", "tags", "homepage", "license", "appVersion", "warning",
    "currentVersion", "versions",
]
LAYOUT_FIELDS = [
    "id", "name", "author", "description", "tags",
    "repo", "homepage", "license", "appVersion", "requiresSchemes",
    "screenshots", "warning", "currentVersion", "versions",
]


# ─── 检查是否有缺失 ──────────────────────────────────────


def check():
    any_needed = False
    for subdir in ("rimes", "plugins/v1", "plugins/v2", "models", "layouts"):
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

# 输出子索引文件头
HEADERS = {
    "rimes": "# Xime 输入方案子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
    "plugins": "# Xime 插件子索引（旧版 Lua/DEX，兼容旧版 App）\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
    "plugins/v2": "# Xime v2 插件子索引（JS/QuickJS 插件，宿主 >=3.0.0）\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
    "models": "# Xime 模型子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
    "layouts": "# Xime 键盘布局子索引\n# ⚠️ 此文件由 scripts/ci-update.py 自动生成，请勿手动编辑\n",
}


def update_source(src_subdir, out_subdir, key, fields, filler, header, index_version=1):
    """从 src/<src_subdir>/ 读源码 → 补全 checksum → 输出 <out_subdir>/index.yaml（不修改 src/）。

    src 与 out 显式分离，便于归档：
      - src/plugins/v1 → plugins/index.yaml    旧版稳定 URL（旧 App 硬编码，不可改动）
      - src/plugins/v2 → plugins/v2/index.yaml v2 新索引
    """
    from datetime import date
    today = date.today().isoformat()

    src_dir = os.path.join(SRC_DIR, src_subdir)
    out_dir = os.path.join(ROOT, out_subdir)

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

        print(f"  📄 src/{src_subdir}/{basename}")
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

    os.makedirs(out_dir, exist_ok=True)
    index = {"index_version": index_version, "updated_at": today, key: entries}
    yaml_str = yaml.dump(index, allow_unicode=True, default_flow_style=False, sort_keys=False)
    index_path = os.path.join(out_dir, "index.yaml")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(header + yaml_str)
    print(f"  ✓ 已重新生成 {out_subdir}/index.yaml ({len(entries)} 条目)")


def update():
    print("=" * 50)
    print("🔄 CI 自动补全 sha256/size/sizeBytes")
    print("=" * 50)

    update_source("rimes", "rimes", "schemas", SCHEMA_FIELDS, fill_download_urls, HEADERS["rimes"])
    print()
    # 旧版插件：源归档在 src/plugins/v1，发布到旧 App 硬编码读取的 plugins/index.yaml
    update_source("plugins/v1", "plugins", "plugins", PLUGIN_FIELDS, fill_download_urls, HEADERS["plugins"])
    print()
    # v2 插件：源在 src/plugins/v2，发布到 plugins/v2/index.yaml
    update_source(
        "plugins/v2", "plugins/v2", "plugins", PLUGIN_V2_FIELDS, fill_download_urls,
        HEADERS["plugins/v2"], index_version=2,
    )
    print()
    update_source(
        "models", "models", "models", MODEL_FIELDS,
        lambda d: recalc_model_size(fill_files_checksums(fill_archive(d))), HEADERS["models"],
    )
    print()
    update_source("layouts", "layouts", "layouts", LAYOUT_FIELDS, fill_download_urls, HEADERS["layouts"])

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
