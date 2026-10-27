#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资源总库链接体检：并发检测 app/library-data.js 全部外链。
只把「确认死亡」的链接列为 suspect（404/解析失败/连续拒连）；
反爬类响应（403/412/429/999/超时）标记 blocked，不算死链。
用法：python tools/linkcheck.py [输出json]  （默认 _linkreport.json）
"""
import json, re, sys, time, urllib.request, urllib.error, socket, ipaddress
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

socket.setdefaulttimeout(14)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
      'Accept-Language': 'zh-CN,zh;q=0.9'}

BLOCK_CODES = {401, 403, 405, 406, 412, 418, 429, 451, 503, 999}

# 私网/环回/链路本地/CGNAT/组播黑名单（显式列举，避免 is_private 误伤代理 fake-IP 段）
_BLOCKED_NETS = tuple(ipaddress.ip_network(n) for n in (
    '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
    '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4',
    '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8'))


def _guard(url):
    """体检目标边界校验：仅 http/https，且解析后 IP 不得落在私网/环回/链路本地（防 SSRF）。"""
    u = urllib.parse.urlparse(url)
    if u.scheme not in ('http', 'https'):
        raise ValueError('仅允许 http/https 体检：%s' % url)
    host = (u.hostname or '').lower()
    if not host or host == 'localhost' or host.endswith(('.local', '.internal')):
        raise ValueError('禁止内网主机：%s' % host)
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
        for info in socket.getaddrinfo(host, None):
            hip = ipaddress.ip_address(info[4][0])
            if any(hip in n for n in _BLOCKED_NETS if n.version == hip.version):
                raise ValueError('域名解析到内网地址：%s -> %s' % (host, hip))
    if ip is not None and any(ip in n for n in _BLOCKED_NETS if n.version == ip.version):
        raise ValueError('禁止内网地址体检：%s' % host)
    return url


# 体检要跟踪重定向拿最终状态，用默认 opener（目标已由 _guard 边界校验）
_OPENER = urllib.request.build_opener()

def load_entries(path='app/library-data.js'):
    s = open(path, encoding='utf-8').read()
    pat = re.compile(r"\{t:'([^']*)',u:'([^']*)',d:'([^']*)',g:(\d+),s:'([^']*)',ty:'([^']*)',f:'([^']*)',o:'([^']*)'(?:,w:1)?\}")
    return pat.findall(s)

def probe(url):
    """返回 (final_status, kind) kind in ok/blocked/dead"""
    for attempt in range(3):
        try:
            safe = _guard(url)
            req = urllib.request.Request(safe, headers=UA, method='GET')
            r = _OPENER.open(req, timeout=14)
            return r.status, 'ok'
        except urllib.error.HTTPError as e:
            if e.code in BLOCK_CODES:
                return e.code, 'blocked'
            if e.code == 404 and attempt == 2:
                return 404, 'dead'
            if e.code < 500:
                return e.code, 'blocked' if e.code in BLOCK_CODES else 'dead'
            last = e.code
        except urllib.error.URLError as e:
            last = str(getattr(e, 'reason', e))[:90]
        except Exception as e:
            last = str(e)[:90]
        time.sleep(1.5 * (attempt + 1))
    return last, 'dead'

def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else '_linkreport.json'
    entries = load_entries()
    urls = []
    seen = set()
    for m in entries:
        if m[1] not in seen:
            seen.add(m[1]); urls.append(m[1])
    print('unique urls:', len(urls), flush=True)
    result = {}
    def work(u):
        st, kind = probe(u)
        return u, st, kind
    with ThreadPoolExecutor(max_workers=12) as ex:
        for u, st, kind in ex.map(work, urls):
            result[u] = {'status': st, 'kind': kind}
            mark = {'ok': 'OK ', 'blocked': 'BLK', 'dead': '!!!'}[kind]
            print(f'[{mark}] {st} {u}', flush=True)
    Path(out_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    dead = [u for u, v in result.items() if v['kind'] == 'dead']
    blk = [u for u, v in result.items() if v['kind'] == 'blocked']
    print(f'== done. ok={len(urls)-len(dead)-len(blk)} blocked={len(blk)} dead={len(dead)}', flush=True)
    for u in dead:
        print('DEAD:', u, flush=True)

if __name__ == '__main__':
    main()
