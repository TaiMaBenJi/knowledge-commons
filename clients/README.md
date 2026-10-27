# clients/ —— CloudStudy 多端统一工程

**一个内容源，四端同构发布。** 所有平台共用根目录的 `study.html`（单文件学习中心）
与内容资产（`videos/`、`multiskill/`），由 GitHub Actions 云端流水线构建。

| 端 | 产物 | 构建方式 | 工作流 |
|---|---|---|---|
| Android | `CloudStudy-v3.1-android-full.apk`（全视频离线 · 完整版） | ubuntu + aapt2/d8/apksigner（仓库自带模板） | `.github/workflows/build-android.yml` |
| iOS | `CloudStudy-v3.1-ios-full-unsigned.ipa`（免签名，Sideloadly/AltStore 侧载） | macOS + XcodeGen + xcodebuild | `.github/workflows/build-ios.yml` |
| Windows | `zhishi-gongshe-v3.1-windows-x64.zip`（便携文件夹包：启动器 + study.html + study-data + learn） | ubuntu + zig 交叉编译 | `.github/workflows/build-windows.yml` |
| macOS | `zhishi-gongshe-v3.1-macos-universal.zip`（.app，内容内嵌自包含） | macOS + swiftc | `.github/workflows/build-macos.yml` |
| Linux | `zhishi-gongshe-v3.1-linux-x64.zip`（便携文件夹包，musl 静态启动器） | ubuntu + zig 交叉编译 | `.github/workflows/build-linux.yml` |
| Web | `study.html`（拆分壳）+ `study-data/` / GitHub Pages 门户 | 直接分发 / Pages 托管 | — |

## 内容基线

- 学习中心：`study.html`（拆分壳）+ `study-data/`（manifest + 59 内容块，共 3162 篇）
- 客户端内容打包：
  · Windows / Linux —— 便携文件夹包，启动器打开同目录 `study.html`（`file://` 下内容块经脚本注入加载，已实测可用）
  · Android / iOS / macOS —— 用 `tools/bundle_full_study.py` 把拆分产物重组为**全量内联单文件**再嵌入（file:// 无外部依赖，实测自包含）
- 视频：`videos/`（62 集：机房 15 + 教程 18 + 进阶 29）+ `multiskill/<领域>/<赛项>/总纲课.mp4`（50 集）
- 模拟训练：`multiskill/<领域>/<赛项>/模拟训练.html`（50 个，十题交互评分）
- 引用全部为**相对路径**（`videos/…`、`multiskill/…`），在 Web / APK assets / iOS bundle / 桌面目录下均直接可用

## 云端出包（推荐）

GitHub → Actions → 选 `build-android` / `build-ios` / `build-windows` / `build-linux` / `build-macos` → Run workflow：
- `upload_release`：填 `v3.1` 等 tag → 构建完成自动上传到 Releases（构建即完整版；推 `v*` tag 也会自动触发六端构建并上传）

## 本地出包

```sh
# Windows 便携包（需 zig）：sh clients/windows/build.sh study.html dist/CloudStudy-windows.zip
# Linux 便携包（需 zig）：  sh clients/linux/build.sh study.html dist/CloudStudy-linux.zip
# 全量内联单文件（移动端/macOS 用）：python tools/bundle_full_study.py clients/_full/study.html
# iOS（需 macOS）：见 clients/ios/README.md
# Android（需 Android SDK）：见 clients/android/README.md
```

> 历史设备端构建脚本仍在 `tools/rebuild_apk.sh` / `tools/rebuild_full.sh`（存档参考）。
