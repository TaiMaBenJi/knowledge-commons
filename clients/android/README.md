# clients/android —— Android APK（云端构建）

与其它端**同一内容源**：根目录 `study.html` + `videos/` + `multiskill/`。

## 云端构建（推荐）

Actions → **build-android** → Run workflow，`upload_release` 填 `v3.1` 等 tag 则自动传 Releases（构建完整版；推 `v*` tag 也会自动触发）。

构建细节（`build_ci.sh`，全部在 ubuntu 运行器完成）：

1. 铺 assets：`study.html` + `videos/` + `multiskill/**/{总纲课.mp4,模拟训练.html}`
2. `smali.jar` 汇编 `tools/apk-template/smali` → `classes.dex`
3. SDK `aapt2 compile/link`（`-0 mp4` 视频直通不压缩）
4. `tools/add_dex.py` 合并 dex 进 APK
5. `zipalign` + `apksigner`（签名密钥来自仓库 Secrets：`ANDROID_KS_B64` / `ANDROID_KS_PASS`）

> 签名证书 = `CloudStudy Learning Center`（cloudstudy），与应用历史版本一致，可直接覆盖升级。

## 本机构建

为设备端脚本（aapt2 在手机上跑）：见 `tools/rebuild_apk.sh`、`tools/rebuild_full.sh`（历史存档）。
云端脚本 `clients/android/build_ci.sh` 在本地装有 Android SDK 的机器上同样可用：

```sh
ANDROID_HOME=/path/to/sdk ANDROID_KS_B64="$(base64 -w0 ks.jks)" ANDROID_KS_PASS=... \
  sh clients/android/build_ci.sh
```
