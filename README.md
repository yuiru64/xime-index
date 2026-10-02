# Xime Index

Xime 输入法的插件、方案、模型与键盘布局市场索引。

## 目录结构

```
├── index.yaml                 # 市场主索引（引用子索引）
├── src/                       # 源文件（每个条目一个 YAML）
│   ├── rimes/                 #   输入方案源文件
│   ├── plugins/v1/            #   旧版插件源文件归档（Lua/DEX）
│   ├── plugins/v2/            #   v2 插件源文件（JS/QuickJS，宿主 >=3.0.0）
│   ├── models/                #   模型源文件
│   └── layouts/               #   键盘布局源文件（内容托管在作者仓库，仅存引用）
├── rimes/                     # 方案子索引（自动生成）
│   └── index.yaml
├── plugins/                   # 插件子索引（自动生成）
│   ├── index.yaml             #   旧版插件（Lua/DEX，兼容旧版 App；源在 src/plugins/v1/）
│   └── v2/
│       └── index.yaml         #   v2 插件（JS/QuickJS，宿主 >=3.0.0；源在 src/plugins/v2/）
├── models/                    # 模型子索引（自动生成）
│   └── index.yaml
├── layouts/                   # 键盘布局子索引（自动生成）
│   └── index.yaml
├── scripts/
│   ├── ci-update.py           #   CI 自动补全 sha256/size
│   ├── lib.py                 #   共享工具库
│   ├── build_dist.py          #   组装 Cloudflare Pages 发布目录 dist/
│   └── generate_index.py      #   旧版生成器（已弃用，请用 ci-update.py）
├── dist/                      # Pages 发布产物（build_dist.py 生成，不入库）
├── CONTRIBUTING.md            # 上架指南
├── LAYOUT_SPEC.md             # 键盘布局上架规范
└── .github/workflows/         # CI 校验
```

## 支持情况

### 模型 (Models)

| ID | 名称 | 作者 | 分类 | 大小 | 最低 App 版本 |
|---|---|---|---|---|---|
| `ochwpro` | 手写模型 | bikeand (Kor1 ) | handwriting | 6.7 MB | >=2.5.0 |
| `predictive-text-base` | 智能联想模型 base 版本 | bikeand (Kor1 ) | prediction | 34.8 MB | >=2.6.0 |
| `predictive-text-small` | 智能联想模型 small 版本 | bikeand (Kor1 ) | prediction | 18.9 MB | >=2.3.0 |
| `punctuation_int8` | 标点预测模型 int8 | bikeand (Kor1 ) | punctuation | 2.3 MB | >=2.3.0 |
| `zipformer-zh-int8` | 中文 Zipformer int8 | bikeand (Kor1 ) | asr | 132.6 MB | <2.6.0 |

### 插件 (Plugins，旧版 Lua/DEX)

| ID | 名称 | 作者 | 类型 | 大小 | 最低 App 版本 |
|---|---|---|---|---|---|
| `com.kingzcheung.xime.plugin.funasr_asr` | 阿里百炼 FunAsr | Xime | speech | 10.2 KB | >=2.6.0 |
| `com.kingzcheung.xime.plugin.kaomoji` | 颜文字表情包 | Xime | emoji | 3.22 KB | >=2.6.0 |
| `com.kingzcheung.xime.plugin.meme_bunny` | 恶搞兔表情包 | Xime | emoji | 65 KB | >=2.6.0 |
| `com.kingzcheung.xime.plugin.volc_asr` | 火山引擎流式语音识别 | Xime | speech | 10.6 KB | >=2.6.0 |
| `com.kingzcheung.xime.plugin.webdav_clipboard_sync` | WebDAV 剪贴板同步 | Xime | clipboard_sync | 4.52 KB | >=2.6.0 |
| `com.kingzcheung.xime.plugin.ximed_sync` | ximed 剪贴板同步 | Xime | clipboard_sync | 3.01 KB | >=2.6.0 |

### 插件 v2 (Plugins v2，JS/QuickJS，宿主 >=3.0.0)

新版插件系统（TypeScript/QuickJS，`.xipk` 内含 `manifest.json` + 编译产物 `main.js`）使用独立索引
`plugins/v2/index.yaml`（`index_version: 2`），源文件放在 `src/plugins/v2/`；旧版插件的源文件归档在
`src/plugins/v1/`，发布到旧版稳定 URL `plugins/index.yaml`。索引条目在旧扁平结构上追加了新插件系统的元数据
（`icon` / `activation` / `minHostVersion` / `platforms` / `capabilities` / `network`），
旧版 App 继续读取 `plugins/index.yaml`，互不影响。

| ID | 名称 | 类型 | 大小 | 最低 App 版本 |
|---|---|---|---|---|
| `com.kingzcheung.xime.plugin.ai_reply` | AI 智能回复 | tool | 3.4 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.ai_write` | AI 帮写 | tool | 2.6 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.funasr_asr` | 阿里百炼 FunAsr | speech | 9.3 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.kaomoji` | 颜文字表情包 | emoji | 3.0 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.meme_bunny` | 恶搞兔表情包 | emoji | 65.0 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.quick_phrase` | 常用语 | tool | 1.5 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.qwen_translate` | 千问翻译 | tool | 2.6 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.tencent_asr` | 腾讯云实时语音识别 | speech | 11.6 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.typing_stats` | 输入统计 | tool | 2.5 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.volc_asr` | 火山引擎流式语音识别 | speech | 8.8 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.webdav_backup` | WebDAV 云备份 | backup | 3.7 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.webdav_clipboard_sync` | WebDAV 剪贴板同步 | clipboard_sync | 3.1 KB | >=3.0.0 |
| `com.kingzcheung.xime.plugin.ximed_sync` | ximed 剪贴板同步 | clipboard_sync | 2.2 KB | >=3.0.0 |

### 输入方案 (Rimes)

| ID | 名称 | 作者 | 类型 | 标签 | 最低 App 版本 |
|---|---|---|---|---|---|
| `cangjie` | 倉頡輸入法 | rime | remote | 倉頡 | >=2.3.0 |
| `luna_pinyin` | 朙月拼音 | rime | remote | 拼音, 反查 | >=2.3.0 |
| `quick` | 速成輸入法 | rime | remote | 速成 | >=2.3.0 |
| `rime-ice` | 雾凇拼音 | iDvel | remote | 拼音, 双拼 | >=2.3.0 |
| `rime-wanxiang` | 万象拼音标准版 | amzxyz | remote | 拼音, 双拼 | >=2.4.0 |
| `stroke` | 笔画 | rime | remote | 笔画 | >=2.5.0 |
| `wubi86` | 五笔86 | rime | built-in | 五笔, 拼音 | >=2.3.0 |
| `wubi98` | 五笔98 | rime | remote | 五笔, 形码, 繁体 | >=2.3.0 |
| `zhengma` | 郑码方案 | chen32768 | remote | 郑码, 拼音, 简繁 | >=2.3.0 |

## 工作原理

CI 自动为每个下载链接补全 `sha256`、`size`（人类可读）和 `sizeBytes`（精确字节数），
方便 App 展示文件大小和计算下载进度。`version` 为 `master`/`main` 的分支引用会被跳过（内容不固定）。

## 键盘布局 (Layouts)

布局是「一套 `xime.custom.yaml` 键盘配置」，本索引只保存**引用**，
包与资源托管在作者自有仓库。详见 [LAYOUT_SPEC.md](LAYOUT_SPEC.md)。

| ID | 名称 | 作者 | 标签 | 最低 App 版本 |
|---|---|---|---|---|
| `number_rows` | 数字行 | kingzcheung | 布局 | >=3.0.0 |

## 本地更新

```bash
# 补全 sha256/size 并重新生成索引
python scripts/ci-update.py

# 仅检查是否有缺失
python scripts/ci-update.py --check

# 本地预览 Pages 发布内容（生成 dist/）
python scripts/build_dist.py
```

推送到 `main` 分支时 CI 会自动生成索引、组装 `dist/` 并部署到 Cloudflare Pages，无需手动操作。

> **首次启用 Pages** 需在 Cloudflare 创建项目 `xime-index`：
> `npx wrangler@3.90.0 pages project create xime-index --production-branch=main`。
> 然后把对外域名（如 `index.ximei.me`）绑定到该 Pages 项目；若该域名此前绑定在 Worker 上，需先解除 Worker 的路由，避免冲突。

详见 [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)。

## 上架

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

[CC BY-NC-SA 4.0](LICENSE) — 署名-非商业性使用-相同方式共享

