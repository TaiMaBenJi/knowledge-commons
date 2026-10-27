#!/bin/sh
# stage.sh —— 将内容资源铺入 clients/ios/Resources/（供 Xcode 打包 · 完整版）
#   study.html + videos/ + multiskill/（视频 + 模拟训练 + 图解，约 500MB，全离线）
set -eu
IOS="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$IOS/../.." && pwd)"
cd "$ROOT"

rm -rf "$IOS/Resources"
mkdir -p "$IOS/Resources/videos" "$IOS/Resources/multiskill"

# 1) 单文件学习中心（客户端用全量内联版：tools/bundle_full_study.py 重组，file:// 自包含）
cp -f clients/_full/study.html "$IOS/Resources/study.html"
cp -R learn "$IOS/Resources/learn"

# 2) 内容资产：全量（视频课 + 全技能库视频与模拟训练 + 图解）
cp -R videos/. "$IOS/Resources/videos/"
find multiskill \( -name '*.mp4' -o -name '模拟训练.html' \) -print | while IFS= read -r f; do
  mkdir -p "$IOS/Resources/$(dirname "$f")"
  cp "$f" "$IOS/Resources/$(dirname "$f")/"
done

echo "== staged =="
du -sh "$IOS/Resources" "$IOS/Resources"/*
