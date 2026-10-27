#!/bin/sh
# CloudStudy · Linux 便携文件夹包构建（musl 静态启动器 + 内容完整版随包）
#   CloudStudy + study.html + study-data/ + learn/
# 用法: sh build.sh <study.html> [out.zip]
#   内容目录 = study.html 所在目录（需含 study-data/、learn/）
set -eu
HTML="${1:?用法: sh build.sh <study.html> [out.zip]}"
OUT="${2:-dist/CloudStudy-linux.zip}"
case "$HTML" in /*) ;; *) HTML="$(pwd)/$HTML" ;; esac
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac
DIR="$(cd "$(dirname "$0")" && pwd)"
CONTENT="$(dirname "$HTML")"
ODIR="$(dirname "$OUT")"
STAGE="$ODIR/CloudStudy-linux"
mkdir -p "$ODIR"
rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "== 编译启动器 =="
zig cc -target x86_64-linux-musl -O2 -s \
  -o "$STAGE/CloudStudy" "$DIR/launcher.c"
chmod +x "$STAGE/CloudStudy" || true

echo "== 铺内容 =="
cp -f "$HTML" "$STAGE/study.html"
cp -R "$CONTENT/study-data" "$STAGE/study-data"
if [ -d "$CONTENT/learn" ]; then cp -R "$CONTENT/learn" "$STAGE/learn"; fi

echo "== 打包 =="
rm -f "$OUT"
if command -v zip >/dev/null 2>&1; then
  ( cd "$ODIR" && zip -qr "$(basename "$OUT")" "$(basename "$STAGE")" )
elif command -v 7z >/dev/null 2>&1; then
  7z a -tzip "$OUT" "$STAGE" >/dev/null
elif [ -x "/c/Program Files/7-Zip/7z.exe" ]; then
  "/c/Program Files/7-Zip/7z.exe" a -tzip "$OUT" "$STAGE" >/dev/null
else
  ( cd "$ODIR" && tar -czf "${OUT%.zip}.tar.gz" "$(basename "$STAGE")" )
fi
echo "== 产物 =="
ls -la "$OUT" 2>/dev/null || ls -la "${OUT%.zip}.tar.gz"
