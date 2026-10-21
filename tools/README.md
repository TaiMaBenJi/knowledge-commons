# tools/ —— 构建与质检脚本

约定：脚本都按 **仓库根目录** 为工作目录调用（脚本内用的都是 `tools/xxx` 或根级路径）。
本目录不分类子目录——历史上 CI、文档、页面提示里都直接写死 `tools/xxx.py`，移动会连带改十几处引用。

## 站点构建 / 生成

| 脚本 | 作用 |
|---|---|
| `build_liquid.py` | 生成 liquid-glass 风格资料中心（`study.html` 前身）单文件；末尾自动调用 `split_study.py` |
| `split_study.py` | 把 14MB 单文件拆成 `study-data/manifest.*.js` + `study-data/c/*.js`（首屏 757KB） |
| `add_study_docs.py` | **增量往资料中心插新文档**（不动既有 3161 篇）。清单见 `study_additions.json` |
| `build_sim.js` `sim_template.html` | 生成模拟训练页（世赛赛项） |
| `auto_svg.js` `svg_templates/` | 图解 SVG 批量生成 |
| `mini_lang.py` | 「迷你语言编译器」教学示例（词法/语法/字节码/虚拟机，课程第 19 章配套） |

## 质检

| 脚本 | 作用 |
|---|---|
| `verify_all.py` | **全仓库质量门禁（一键跑完 14 项）**：脚本行尾 / bash 语法 / js 语法 / tools 语法 / 站内体检 / md 路径引用 / md 章节结构 / md 代码块语法 / md yaml / md 代码块实跑 / manifest 一致性 / 增量文档 / 数字一致性 / PWA 预缓存 |
| `internal_qa.py` | 单项全站内部体检（HTML/MD 内链 · 预缓存 · 检索索引 · sitemap · JSON · JS） |
| `add_study_docs.py` | **增量往资料中心插新文档**（不动既有 3161 篇）。清单见 `study_additions.json` |
| `linkcheck.py` | 资源总库全部外链并发体检（403/412/429/999 判为 blocked，不算死链） |
| `qc/full_media_probe.py` | 全部视频逐部解码体检（0 错误为通过） |

## 数据采集

| 脚本 | 作用 |
|---|---|
| `bili_collect.py` `bili_to_js.py` | B 站精选视频采集 → 页面数据 |
| `make_video.py` | 视频合成辅助 |

## Android 打包（客户端构建链）

| 脚本 | 作用 |
|---|---|
| `rebuild_apk.sh` `rebuild_full.sh` `build_dev.sh` `chain_guard.sh` | APK 重建链（分步/全量/开发/串行守卫） |
| `add_dex.py` `android_namefix.py` | 合并 dex、把非 ASCII 资源名转义为 `_uXXXX` 并同步改写引用（部分 Android WebView 读不了中文路径） |
| `apk-template/` `prebuilt/` `jars/smali.jar` | 模板工程、预置 dex 与 smali 工具 |
