"""
共享工具库 — 供各构建子脚本调用。
"""

import glob
import hashlib
import os
import re
import tempfile
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_VERSIONS = {"master", "main"}
USER_AGENT = "Xime-Index-Checksum/1.0"

BASE_GIT_PROXY = "https://gh-proxy.org/"

def enable_proxy(versions):
    if not isinstance(versions, list): return []
    
    new_versions = []
    for version in versions:
        if not isinstance(version, dict): continue
        if "downloadUrl" in version:
            key = "downloadUrl"
        elif "files" in version:
            key = "files"
        else:
            continue

        files = version[key]
        if not isinstance(files, list): continue
        
        new_files = []
        for url_entry in files:
            if not isinstance(url_entry, dict): continue
            if "url" not in url_entry: continue
            if re.match("^https://github.com/.*$", url_entry["url"]):
                new_url = BASE_GIT_PROXY + url_entry["url"]
                new_files.append({**url_entry, "url": new_url})
            else:
                new_files.append(url_entry.copy())
        
        new_versions.append({**version, key: new_files})
        return new_versions

def human_size(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def download_checksum(url: str):
    """下载文件，返回 (sha256_hex, size_bytes, size_human)。"""
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp()
        os.close(fd)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=300) as resp:
            sha256 = hashlib.sha256()
            size_bytes = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)
                size_bytes += len(chunk)
        return sha256.hexdigest(), size_bytes, human_size(size_bytes)
    except Exception as exc:
        print(f"    ⚠ 下载失败: {exc}")
        return None, None, None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def should_skip_version(version: str) -> bool:
    return version.strip().strip('"').strip("'") in SKIP_VERSIONS


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def fill_download_urls(data: dict) -> dict:
    """
    补全 data 中 downloadUrl 列表内缺失的 sha256/size/sizeBytes。
    跳过 version 为 master/main 的版本。
    返回新的 dict（深拷贝），不修改入参。
    """
    import copy
    result = copy.deepcopy(data)

    for v in result.get("versions", []):
        ver = v.get("version", "?")
        if should_skip_version(ver):
            continue

        for dl in v.get("downloadUrl", []):
            url = dl.get("url", "")
            if not url or (dl.get("sha256") and dl.get("size")):
                continue
            # 跳过 .gram 文件，不生成 sha256
            if url.endswith(".gram"):
                print(f"  ⏭ {url} (.gram 文件，跳过 sha256)")
                continue
            print(f"  ↓ {url}")
            sha256, size_bytes, size_h = download_checksum(url)
            if sha256:
                dl["sha256"] = sha256
                dl["size"] = size_h
                dl["sizeBytes"] = size_bytes
                print(f"    ✓ sha256={sha256[:16]}...  size={size_h}  bytes={size_bytes}")

    return result


def fill_archive(data: dict) -> dict:
    """
    补全 data 中 archive 块缺失的 sha256/size/sizeBytes。
    跳过 version 为 master/main 的版本。
    """
    import copy
    result = copy.deepcopy(data)

    for v in result.get("versions", []):
        ver = v.get("version", "?")
        if should_skip_version(ver):
            continue

        if "archive" in v:
            a = v["archive"]
            url = a.get("url", "")
            if url and (not a.get("sha256") or not a.get("size")):
                print(f"  ↓ {url}")
                sha256, size_bytes, size_h = download_checksum(url)
                if sha256:
                    a["sha256"] = sha256
                    a["size"] = size_h
                    a["sizeBytes"] = size_bytes
                    print(f"    ✓ sha256={sha256[:16]}...  size={size_h}  bytes={size_bytes}")

    return result


def fill_files_checksums(data: dict) -> dict:
    """
    补全 data 中 files 列表内缺失的 sha256/size/sizeBytes。
    跳过 version 为 master/main 的版本。
    """
    import copy
    result = copy.deepcopy(data)

    for v in result.get("versions", []):
        ver = v.get("version", "?")
        if should_skip_version(ver):
            continue

        for f_item in v.get("files", []):
            url = f_item.get("url", "")
            if not url or (f_item.get("sha256") and f_item.get("size")):
                continue
            print(f"  ↓ {url}")
            sha256, size_bytes, size_h = download_checksum(url)
            if sha256:
                f_item["sha256"] = sha256
                f_item["size"] = size_h
                f_item["sizeBytes"] = size_bytes
                print(f"    ✓ sha256={sha256[:16]}...  size={size_h}  bytes={size_bytes}")

    return result


def recalc_model_size(data: dict) -> dict:
    """
    重新计算模型级 size = 所有版本中所有文件 sizeBytes 的总和。
    仅在 sizeBytes 齐全时生效。
    """
    import copy
    result = copy.deepcopy(data)

    total_bytes = 0
    has_all = True
    for v in result.get("versions", []):
        for f in v.get("files", []):
            sb = f.get("sizeBytes")
            if sb is None:
                has_all = False
            else:
                total_bytes += sb

    if has_all and total_bytes > 0:
        old = result.get("size")
        new = human_size(total_bytes)
        result["size"] = new
        if old != new:
            print(f"    📐 模型大小: {old} → {new}")

    return result
