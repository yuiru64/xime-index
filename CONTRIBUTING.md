# 贡献指南

通过 PR 添加或更新文件即可上架方案或插件。

## 目录结构

```
src/                          # 所有条目的源文件（每个条目一个独立 YAML）
├── rimes/                    #   输入方案源文件
├── plugins/v1/               #   旧版插件源文件归档（Lua/DEX）
├── plugins/v2/               #   v2 插件源文件（JS/QuickJS，宿主 >=3.0.0）
├── models/                   #   AI 模型源文件
└── layouts/                  #   键盘布局源文件

rimes/index.yaml              # 方案子索引（由 scripts/ci-update.py 自动生成，请勿手动编辑）
plugins/index.yaml            # 旧版插件子索引（源在 src/plugins/v1/，自动生成）
plugins/v2/index.yaml         # v2 插件子索引（源在 src/plugins/v2/，自动生成）
models/index.yaml             # 模型子索引（自动生成）
layouts/index.yaml            # 键盘布局子索引（自动生成）
```

## 上架新方案

### 步骤 1：创建方案文件

在 `rimes/` 下新建 `<id>.yaml` 文件：

```yaml
# rimes/my_schema.yaml
id: "my_schema"                  # 方案 ID，与 schema_id 一致
name: "我的方案"                  # 显示名称
author: "你的名字"                # 作者
description: "方案说明"           # 简短描述
type: "remote"
tags: ["五笔"]                    # 搜索标签
homepage: "https://..."          # 项目主页（可选）
license: "GPL-3.0"               # 许可证（可选）
dependencies: []                  # 依赖的其他方案 ID
appVersion: ">=2.2.0"            # 兼容的 App 版本
warning: ""                       # 安装前警告（可选）
currentVersion: "1.0.0"          # 当前版本
versions:                         # 版本历史
  - version: "1.0.0"
    date: "2026-06-01"           # 发布日期
    changelog: "初始发布"          # 更新说明
    downloadUrl:                  # 下载地址
      - url: "https://..."       # 单个文件时只写一条
        sha256: ""               # SHA256 校验值（可选）
        size: "1.5 MB"           # 文件大小（可选）
```

### 步骤 2：生成索引

```bash
python scripts/ci-update.py
```

`rimes/index.yaml` 会自动更新，包含新方案的完整信息。

## 上架旧版插件（Lua/DEX）

旧版插件源文件归档在 `src/plugins/v1/`，生成 `plugins/index.yaml` 供旧版 App 使用，请勿移除。

### 步骤 1：创建插件文件

在 `src/plugins/v1/` 下新建 `<id>.yaml` 文件：

```yaml
# src/plugins/v1/my-plugin.yaml
id: "xime.my-plugin"             # 插件唯一 ID
name: "我的插件"                  # 显示名称
author: "你的名字"                # 作者
description: "插件说明"           # 简短描述
type: "remote"
tags: ["表情"]                    # 搜索标签
pluginType: "emoji"              # 插件类型
homepage: "https://..."          # 项目主页（可选）
license: "MIT"                   # 许可证（可选）
appVersion: ">=2.3.0"            # 兼容的 App 版本
currentVersion: "1.0.0"
versions:
  - version: "1.0.0"
    date: "2026-06-01"
    changelog: "初始发布"
    downloadUrl:                  # 下载地址
      - url: "https://..."       # 单个文件时只写一条
        sha256: ""               # SHA256 校验值（可选）
        size: ""                 # 文件大小（可选）
```

### 步骤 2：生成索引

```bash
python scripts/ci-update.py
```

`plugins/index.yaml` 会自动更新。

## 上架 v2 插件（JS/QuickJS，宿主 >=3.0.0）

v2 插件是 TypeScript/QuickJS 形态：源码为 `manifest.json` + `main.ts`（由 `xipm pack` 产出 `.xipk`，
包内含 `manifest.json` + 编译产物 `main.js` + `resources/`）。它们使用独立索引
`plugins/v2/index.yaml`（源文件放在 `src/plugins/v2/`），旧版 App 不受影响。

### 步骤 1：创建插件源文件

在 `src/plugins/v2/` 下新建 `<id>.yaml` 文件，除旧版字段外，另填新插件系统的元数据：

```yaml
# src/plugins/v2/my-plugin.yaml
id: com.example.xime.plugin.my_plugin
name: 我的插件
author: Xime
description: "插件说明"
type: remote                     # 下载类型，固定 remote
tags: [工具]
pluginType: tool                 # 与插件 manifest 的 type 一致：tool/speech/emoji/backup/clipboard_sync...
icon: "我"                        # manifest.icon：字符图标或 resources 下的图片名
activation: multi                # manifest.activation：single / multi
minHostVersion: '3.0.0'          # manifest.minHostVersion
platforms: [android]             # manifest.platforms
capabilities:                    # 原样取自 manifest.capabilities
  tool:
    display: passive
network:                         # 原样取自 manifest.network（可省略）
  allowCustomHosts: true
homepage: https://github.com/ximeiorg/Xime
license: GPL-3.0
appVersion: '>=3.0.0'            # 与 minHostVersion 对应，供 App 兼容性判定
currentVersion: 1.0.0
versions:
  - version: 1.0.0
    date: '2026-09-24'
    changelog: v3 重构：TypeScript/QuickJS 插件
    downloadUrl:
      - url: https://github.com/ximeiorg/Xime/releases/download/v3.0.0-beta1/my-plugin-1.0.0.xipk
        sha256: ""               # 可留空，CI 自动补全
        size: ""                 # 可留空，CI 自动补全
```

> `plugins/v2/index.yaml` 的 `index_version` 为 `2`，条目是旧扁平结构的超集，
> 追加 `icon` / `activation` / `minHostVersion` / `platforms` / `capabilities` / `network`。

### 步骤 2：生成索引

```bash
python scripts/ci-update.py
```

`plugins/v2/index.yaml` 会自动更新并补全 `sha256`/`size`/`sizeBytes`。

## 上架新模型

### 步骤 1：创建模型文件

在 `models/` 下新建 `<id>.yaml` 文件。

**文件列表型模型**（每个文件独立下载）：

```yaml
# models/my-model.yaml
id: "my-model"                      # 模型唯一 ID
name: "我的模型"                     # 显示名称
author: "你的名字"                   # 作者
homepage: "https://..."             # 项目主页（可选）
description: "模型说明"               # 简短描述
category: "prediction"              # 分类：prediction / asr / punctuation / stroke / other
size: "30 MB"                       # 模型大小描述
type: "remote"
tags: ["AI", "ONNX"]                # 搜索标签
appVersion: ">=2.3.0"               # 兼容的 App 版本
currentVersion: "v1.0"
versions:
  - version: "v1.0"
    date: "2026-06-01"
    changelog: "初始发布"
    storageDir: ""                   # 存储相对路径（"" 表示 filesDir 根目录）
    files:
      - name: "model.onnx"          # 每个文件独立 URL
        url: "https://..."
        sha256: ""
        size: ""
      - name: "vocab.json"
        url: "https://..."
        sha256: ""
        size: ""
```

**归档型模型**（通过 tar.bz2 整包下载）：

```yaml
# models/my-asr-model.yaml
id: "my-asr-model"
name: "语音识别模型"
author: "你的名字"                   # 作者
homepage: "https://..."             # 项目主页（可选）
description: "基于 sherpa-onnx 的语音识别模型"
category: "asr"
size: "36 MB"
type: "remote"
tags: ["语音", "sherpa-onnx"]
appVersion: ">=2.3.0"
currentVersion: "v1.0"
versions:
  - version: "v1.0"
    date: "2026-06-01"
    changelog: "初始发布"
    storageDir: "asr_models/my-asr-model"
    archive:                         # 归档包信息
      url: "https://..."
      sha256: ""
      size: "36 MB"
    files:
      - name: "encoder.onnx"        # 归档内的文件（用于校验）
      - name: "decoder.onnx"
      - name: "tokens.txt"
```

**`category` 可选值：**

| 值 | 说明 |
|------|------|
| `prediction` | 智能联想词预测 |
| `asr` | 语音识别 |
| `punctuation` | 标点预测 |
| `stroke` | 笔画序列 (预留) |
| `other` | 其他 |

### 步骤 2：生成索引

```bash
python scripts/ci-update.py
```

`models/index.yaml` 会自动更新。

## 上架新布局

布局（键盘配置）与方案/插件不同：**内容托管在作者自己的仓库**，本索引只保存引用。
完整规范见 [LAYOUT_SPEC.md](LAYOUT_SPEC.md)。

### 步骤 1：创建布局源文件

在 `src/layouts/` 下新建 `<id>.yaml` 文件：

```yaml
# src/layouts/my_layout.yaml
id: my_layout
name: 我的布局
author: yourname
description: 一段简短说明
tags: [布局]                      # 布局 | 配色 | 快捷键 | 输入法适配
repo: https://github.com/you/my-layout   # 作者仓库（内容来源）
license: MIT
appVersion: ">=3.0.0"
requiresSchemes: []               # 依赖的输入方案 id，如 [cangjie]
screenshots:                      # 1~5 张，仅详情页展示
  - https://.../01.png
currentVersion: "1.0.0"
versions:
  - version: "1.0.0"
    date: "2026-09-24"
    changelog: 初始发布
    downloadUrl:
      - url: https://.../xime.custom.yaml   # 纯文本；或用 zip 包（含 themes/fonts）
        sha256: ""
        size: ""
```

### 步骤 2：生成索引

```bash
python scripts/ci-update.py
```

`layouts/index.yaml` 会自动更新并补全 `sha256`/`size`。

## 更新版本

已有方案/插件/模型发布新版本时：

1. 在对应 `.yaml` 文件的 `versions` 列表顶部新增一条版本记录
2. 更新 `currentVersion` 为最新版本号
3. 运行 `python scripts/ci-update.py` 同步索引

## 打包要求

| 类型 | 格式 | 要求 |
|------|------|------|
| 方案 | .zip / .tar.gz | 包含 .schema.yaml + .dict.yaml |
| 插件（旧版） | .xipk | Lua/DEX 插件，兼容旧版 App |
| 插件 v2 | .xipk | `manifest.json` + 编译产物 `main.js`（`xipm pack` 产物），宿主 >=3.0.0 |
| 布局 | xime.custom.yaml 或 .zip | 纯文本直接给 yaml；含 themes/fonts 资源时打 zip（根级 xime.custom.yaml） |

## 下载地址

`downloadUrl` 统一使用对象列表格式，每个文件独立携带 `sha256` 和 `size`。

**单个文件：**
```yaml
downloadUrl:
  - url: "https://example.com/releases/v1.0.0/file.zip"
    sha256: "abc123..."            # 可选
    size: "10 MB"                  # 可选
```

**多个文件全部必装：**
```yaml
downloadUrl:
  - url: "https://example.com/releases/v1.0.0/schema.zip"
    sha256: "abc123..."
    size: "10 MB"
  - url: "https://example.com/releases/v1.0.0/model.gram"
    sha256: "def456..."
    size: "50 MB"
```

**多个文件让用户二选一（带 `name` 标签）：**
```yaml
downloadUrl:
  - name: "基础版"
    url: "https://example.com/releases/v1.0.0/base.zip"
    sha256: "abc123..."
    size: "10 MB"
  - name: "完整版"
    url: "https://example.com/releases/v1.0.0/full.zip"
    sha256: "def456..."
    size: "50 MB"
```



## 注意事项

- 下载地址推荐使用 GitHub Releases，确保长期有效
- 方案若依赖其他方案，在 `dependencies` 中声明，安装时会自动处理
- 子索引由脚本自动生成，不要手动编辑 `rimes/index.yaml`、`plugins/index.yaml` 或 `models/index.yaml`
- 每个版本独立填写 `downloadUrl`，建议指向具体 Release Tag 而非 `latest`
