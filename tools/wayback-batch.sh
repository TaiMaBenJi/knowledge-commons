#!/system/bin/sh
# Wayback Machine 批量存档队列（Save Page Now 匿名接口，限速版）
# 用法：sh tools/wayback-batch.sh [起止行号]
# 说明：匿名 SPN 限速约每分钟数次；全量 1200+ URL 建议分多晚跑完
#       已有快照的 URL 会被 IA 自动跳过，重复执行安全
S=/data/local/tmp
UA="Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"
FROM=${1:-1}
TO=${2:-1217}
node -e '
const fs=require("fs");
const s=fs.readFileSync(process.argv[1],"utf8");
const urls=[...new Set([...s.matchAll(/u:'"'"'([^'"'"']+)'"'"'/g)].map(m=>m[1]))];
console.log(urls.join("\n"));' "$(dirname "$0")/../app/library-data.js" > "$S/wb-urls.txt" 2>/dev/null || \
node -e '
const fs=require("fs");
const s=fs.readFileSync("app/library-data.js","utf8");
const urls=[...new Set([...s.matchAll(/u:'"'"'([^'"'"']+)'"'"'/g)].map(m=>m[1]))];
console.log(urls.join("\n"));' > "$S/wb-urls.txt"
total=$(wc -l < "$S/wb-urls.txt")
echo "queue: $total urls, running $FROM..$TO"
n=0
sed -n "${FROM},${TO}p" "$S/wb-urls.txt" | while IFS= read -r url; do
  n=$((n+1))
  res=$(curl -4 -s --max-time 30 -A "$UA" -o /dev/null -w '%{http_code}' "https://web.archive.org/save/$url" 2>/dev/null)
  echo "[$FROM+$n] $res $url"
  sleep 8
done
echo "BATCH-DONE"
