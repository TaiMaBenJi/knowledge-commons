#!/system/bin/sh
# 知识公社 · 全库链接审计工具（可复用）
# 用法：sh tools/link-audit.sh   （输出状态分布 + 异常清单到 /data/local/tmp/）
# 依赖：curl、busybox xargs；node 用于提取 URL
S=/data/local/tmp/linkaudit-$(date +%s)
mkdir -p "$S"
node -e '
const fs=require("fs");
const s=fs.readFileSync(__dirname+"/../app/library-data.js","utf8");
const urls=[...s.matchAll(/u:'"'"'([^'"'"']+)'"'"'/g)].map(m=>m[1]);
console.log([...new Set(urls)].join("\n"));' > "$S/urls.txt" 2>/dev/null || \
node -e '
const fs=require("fs"),path=require("path");
const s=fs.readFileSync(path.join(process.cwd(),"app/library-data.js"),"utf8");
const urls=[...s.matchAll(/u:'"'"'([^'"'"']+)'"'"'/g)].map(m=>m[1]);
console.log([...new Set(urls)].join("\n"));' > "$S/urls.txt"
echo "unique urls: $(wc -l < "$S/urls.txt")"
cat > "$S/check.sh" <<'SH'
#!/system/bin/sh
UA="Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"
url="$1"
code=$(curl -4 -sL --max-time 15 -A "$UA" -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
if [ "$code" = "000" ] || [ "$code" = "403" ] || [ "$code" = "429" ] || [ "$code" = "503" ]; then
  sleep 1
  code=$(curl -4 -sL --max-time 15 -A "$UA" -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
fi
echo "$code $url"
SH
chmod +x "$S/check.sh"
xargs -P 12 -n 1 "$S/check.sh" < "$S/urls.txt" > "$S/result.txt" 2>/dev/null
echo "=== 状态分布 ==="
awk '{print $1}' "$S/result.txt" | sort | uniq -c | sort -rn
echo "=== 非 200 清单（反爬/登录墙/需国际网络者多为存活，勿直接删除）==="
grep -v '^200 ' "$S/result.txt"
echo "=== 报告目录: $S ==="
