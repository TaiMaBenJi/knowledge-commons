#!/bin/sh
# CloudStudy · Android APK 云端构建脚本（GitHub Actions ubuntu 运行器）
# 用法: sh clients/android/build_ci.sh   （构建完整版：全视频离线）
# 依赖: 仓库内 study.html（统一内容）+ videos/ + multiskill/ + tools/ 材料 + secrets 签名
set -eu
VARIANT="full"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p dist build

# ---------- 定位 Android SDK 工具 ----------
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
BT="$(ls -d "$SDK"/build-tools/* 2>/dev/null | sort -V | tail -1)"
PLATFORM="$(ls -d "$SDK"/platforms/android-* 2>/dev/null | sort -V | tail -1)"
AAPT2="$BT/aapt2"; ZIPALIGN="$BT/zipalign"; APKSIGNER="$BT/apksigner"
ANDROID_JAR="$PLATFORM/android.jar"
echo "SDK=$SDK"; echo "build-tools=$BT"; echo "platform=$PLATFORM"
[ -x "$AAPT2" ] || { echo "FATAL: aapt2 未找到"; exit 1; }
[ -f "$ANDROID_JAR" ] || { echo "FATAL: android.jar 未找到"; exit 1; }
test -f study.html || { echo "FATAL: 缺少 study.html"; exit 1; }

echo "$ANDROID_KS_B64" | base64 -d > build/ks.jks

build_one() {
  V="$1"
  echo "======== 构建 $V ========"
  rm -rf build/ci && mkdir -p build/ci/assets build/ci/res
  cp tools/apk-template/AndroidManifest.xml build/ci/
  cp -r tools/apk-template/smali build/ci/smali
  cp -r tools/apk-template/res/. build/ci/res/
  # 客户端用全量内联单文件（tools/bundle_full_study.py 重组；file:// 下自包含）
  cp clients/_full/study.html build/ci/assets/study.html

  mkdir -p build/ci/assets/videos
  cp -R videos/. build/ci/assets/videos/
  find multiskill \( -name '*.mp4' -o -name '模拟训练.html' \) -print | while IFS= read -r f; do
    mkdir -p "build/ci/assets/$(dirname "$f")"
    cp "$f" "build/ci/assets/$(dirname "$f")/"
  done
  cp -R learn build/ci/assets/
  echo "[$V] assets = $(du -sh build/ci/assets | cut -f1)"

  echo "[$V] dex (prebuilt · 与真机验证版一致)"
  cp tools/prebuilt/classes.dex build/ci/classes.dex
  ls -la build/ci/classes.dex

  echo "[$V] aapt2 compile + link"
  ( cd build/ci && "$AAPT2" compile --dir res -o res.zip \
    && "$AAPT2" link -o out.apk -I "$ANDROID_JAR" --manifest AndroidManifest.xml -0 mp4 -A assets res.zip )
  ls -la build/ci/out.apk

  echo "[$V] merge dex"
  python3 tools/add_dex.py build/ci/out.apk build/ci/classes.dex build/ci/unsigned.apk
  echo "[$V] namefix (ASCII 化非 ASCII 资源名 + 改写 study.html 引用)"
  python3 tools/android_namefix.py build/ci/unsigned.apk build/ci/unsigned-named.apk

  echo "[$V] zipalign + sign"
  "$ZIPALIGN" -f 4 build/ci/unsigned-named.apk build/ci/aligned.apk
  "$APKSIGNER" sign --ks build/ks.jks \
    --ks-pass "pass:$ANDROID_KS_PASS" --key-pass "pass:$ANDROID_KS_PASS" \
    --ks-key-alias cloudstudy \
    --out "dist/zhishi-gongshe-v3.1-android-$V.apk" build/ci/aligned.apk
  "$APKSIGNER" verify "dist/zhishi-gongshe-v3.1-android-$V.apk"
  ls -la "dist/zhishi-gongshe-v3.1-android-$V.apk"
}

build_one "$VARIANT"

rm -f build/ks.jks
echo "===== dist ====="
ls -la dist/
