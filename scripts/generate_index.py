#!/usr/bin/env python3
"""
Xime Index 生成器
扫描 rimes/*.yaml 和 plugins/*.yaml，读取完整数据，
生成包含全部字段的内联索引文件。

用法:
  python scripts/generate_index.py              # 生成索引文件
  python scripts/generate_index.py --check      # CI 检查模式
  python scripts/generate_index.py --validate   # 仅校验数据完整性（可选）
"""

import yaml
import glob
import os
import sys
from datetime import date

from lib import enable_proxy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")
TODAY = date.today().isoformat()

SKIP = {"index.yaml"}

# 字段白名单及输出顺序
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

# ─── 辅助函数 ────────────────────────────────────────────


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


# ─── 收集 ────────────────────────────────────────────────


def collect_entries(subdir, fields, src_subdir=None):
    """扫描源目录下的所有 .yaml 文件，提取指定字段"""
    if src_subdir is None:
        src_subdir = subdir
    entries = []
    pattern = os.path.join(SRC_DIR, src_subdir, "*.yaml")
    for fpath in sorted(glob.glob(pattern)):
        basename = os.path.basename(fpath)
        if basename in SKIP:
            continue
        data = load_yaml(fpath)

        # id 必须与文件名一致
        expected_id = os.path.splitext(basename)[0]
        if data.get("id") != expected_id:
            print(f"⚠  {basename}: id '{data.get('id')}' != '{expected_id}', 跳过")
            continue

        entry = {}
        for field in fields:
            if field in data and data[field] is not None:
                if field == "versions":
                    entry[field] = enable_proxy(data[field])
                else:
                    entry[field] = data[field]
        entries.append(entry)

    # type: built-in 优先排在前面，其余按 id 排序
    entries.sort(
        key=lambda e: (
            e.get("type") != "built-in",
            e.get("id", ""),
        )
    )
    return entries


# ─── 生成 ────────────────────────────────────────────────


HEADERS = {
    "rimes": (
        "# Xime 输入方案子索引\n"
        "# ⚠️ 此文件由 scripts/generate_index.py 自动生成，请勿手动编辑\n"
    ),
    "plugins": (
        "# Xime 插件子索引\n"
        "# ⚠️ 此文件由 scripts/generate_index.py 自动生成，请勿手动编辑\n"
    ),
    "models": (
        "# Xime 模型子索引\n"
        "# ⚠️ 此文件由 scripts/generate_index.py 自动生成，请勿手动编辑\n"
    ),
}


def generate_index(subdir, key, fields, src_subdir=None):
    """生成合并后的索引文件"""
    if src_subdir is None:
        src_subdir = subdir
    index_path = os.path.join(ROOT, subdir, "index.yaml")
    existing = load_yaml(index_path) if os.path.exists(index_path) else {}
    entries = collect_entries(subdir, fields, src_subdir)

    index = {
        "index_version": existing.get("index_version", 1),
        "updated_at": TODAY,
        key: entries,
    }

    # 先写文件头注释，再写 YAML 内容
    header = HEADERS.get(subdir, "")
    yaml_str = yaml.dump(
        index,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(header + yaml_str)


# ─── 校验 ────────────────────────────────────────────────


def validate_index(subdir, key):
    """校验生成的索引数据完整性（取代 CI 中的 Python inline 脚本）"""
    index_path = os.path.join(ROOT, subdir, "index.yaml")
    data = load_yaml(index_path)
    assert data.get("index_version") == 1, f"{subdir}/index.yaml: index_version must be 1"
    assert key in data, f"{subdir}/index.yaml: missing '{key}'"

    items = data[key]
    for entry in items:
        assert "id" in entry, f"{subdir}: missing id in entry"
        assert "name" in entry, f"{entry['id']}: missing name"
        assert "currentVersion" in entry, f"{entry['id']}: missing currentVersion"
        assert "versions" in entry, f"{entry['id']}: missing versions"

        for v in entry["versions"]:
            assert "version" in v, f"{entry['id']}: version entry missing 'version'"
            assert "date" in v, f"{entry['id']} v{v['version']}: missing date"

            if entry.get("type") == "remote":
                dl = v.get("downloadUrl")
                assert dl, f"{entry['id']} v{v['version']}: missing downloadUrl"
                assert isinstance(dl, list), f"{entry['id']} v{v['version']}: downloadUrl must be a list"
                assert len(dl) > 0, f"{entry['id']} v{v['version']}: downloadUrl is empty"
                for i, item in enumerate(dl):
                    assert isinstance(item, dict), f"{entry['id']} v{v['version']} downloadUrl[{i}]: must be object"
                    assert "url" in item, f"{entry['id']} v{v['version']} downloadUrl[{i}]: missing url"

        # plugins 特有
        if key == "plugins":
            assert "pluginType" in entry, f"{entry['id']}: missing pluginType for plugin"

    print(f"  {subdir}/index.yaml: {len(items)} entries, all valid")
    return True


def validate_model_index(subdir, key):
    """校验生成的模型索引数据完整性"""
    index_path = os.path.join(ROOT, subdir, "index.yaml")
    data = load_yaml(index_path)
    assert data.get("index_version") == 1, f"{subdir}/index.yaml: index_version must be 1"
    assert key in data, f"{subdir}/index.yaml: missing '{key}'"

    items = data[key]
    for entry in items:
        assert "id" in entry, f"{subdir}: missing id in entry"
        assert "name" in entry, f"{entry['id']}: missing name"
        assert "category" in entry, f"{entry['id']}: missing category"
        assert "currentVersion" in entry, f"{entry['id']}: missing currentVersion"
        assert "versions" in entry, f"{entry['id']}: missing versions"

        for v in entry["versions"]:
            assert "version" in v, f"{entry['id']}: version entry missing 'version'"
            assert "date" in v, f"{entry['id']} v{v['version']}: missing date"
            assert "storageDir" in v, f"{entry['id']} v{v['version']}: missing storageDir"
            assert "files" in v, f"{entry['id']} v{v['version']}: missing files"
            assert isinstance(v["files"], list), f"{entry['id']} v{v['version']}: files must be a list"

            for f in v["files"]:
                assert "name" in f, f"{entry['id']} v{v['version']}: file entry missing 'name'"
                # archive models don't need individual file URLs, non-archive models do
                if "archive" not in v:
                    assert "url" in f, f"{entry['id']} v{v['version']} file '{f.get('name')}': missing url"

        print(f"  {entry['id']}: valid ({len(v['files'])} files{' (archive)' if 'archive' in v else ''})")

    print(f"  {subdir}/index.yaml: {len(items)} entries, all valid")
    return True


# ─── 主入口 ──────────────────────────────────────────────


def main():
    args = set(sys.argv[1:])
    check_only = "--check" in args
    validate_only = "--validate" in args

    SUBDIRS = ("rimes", "plugins", "models")

    # 暂存当前内容（用于 check 模式）
    snapshots = {}
    if check_only:
        for subdir in SUBDIRS:
            idx = os.path.join(ROOT, subdir, "index.yaml")
            if os.path.exists(idx):
                with open(idx, encoding="utf-8") as f:
                    snapshots[subdir] = f.read()

    # 生成
    generate_index("rimes", "schemas", SCHEMA_FIELDS)
    generate_index("plugins", "plugins", PLUGIN_FIELDS)
    generate_index("models", "models", MODEL_FIELDS)

    # 校验（生成后自动校验）
    print("Validating generated index files...")
    validate_index("rimes", "schemas")
    validate_index("plugins", "plugins")
    validate_model_index("models", "models")

    # check 模式：检测是否有变动
    if check_only:
        changed = []
        for subdir in SUBDIRS:
            idx = os.path.join(ROOT, subdir, "index.yaml")
            with open(idx, encoding="utf-8") as f:
                current = f.read()
            if current != snapshots.get(subdir):
                changed.append(f"{subdir}/index.yaml")

        if changed:
            print("\n❌ 以下索引文件需要更新，请在本地运行:")
            print("   python scripts/generate_index.py")
            for f in changed:
                print(f"   - {f}")
            sys.exit(1)
        print("✅ 所有索引文件已是最新")

    if check_only or validate_only:
        return  # 不打印额外信息

    print("\n✅ 索引文件已生成:")
    print("   - rimes/index.yaml")
    print("   - plugins/index.yaml")
    print("   - models/index.yaml")


if __name__ == "__main__":
    main()
