#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vf_safe · video-factory 公共安全基座

三条硬约束（本目录所有构建脚本统一走这里）：
1. sh()   —— 子进程一律参数列表 + shell=False，杜绝命令注入；
             拒收字符串调用，防止旧写法悄悄回流。
2. under()—— 变量路径拼接后断言仍在给定根目录之下，防路径穿越。
3. https_url() —— 外部下载 URL 只放行 https 且拒绝内网/环回/链路本地地址（SSRF）。
"""
import ipaddress
import os
import socket
import subprocess
import urllib.parse


def sh(cmd, timeout=1200, cwd=None, check=True):
    """执行外部命令。cmd 必须是参数列表——shell=False，无注入面。
    check=False 时容忍非零退出（如 ffprobe 探测场景，由调用方解析输出判定）。"""
    if isinstance(cmd, str):
        raise TypeError(
            'vf_safe.sh 只接受参数列表（shell=False），不接受命令字符串；'
            '请把 f-string 命令拆成 [exe, arg1, arg2, ...] 形式')
    r = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=timeout, cwd=cwd)
    if r.returncode != 0 and check:
        raise RuntimeError('CMD FAIL: %s\n%s' % (' '.join(cmd)[:200], r.stderr[-1500:]))
    return r.stdout


def sh_err(cmd, timeout=1200, cwd=None, check=True):
    """同 sh()，但返回 stderr 全文——volumedetect 等把结果写 stderr 的探测用。"""
    if isinstance(cmd, str):
        raise TypeError(
            'vf_safe.sh_err 只接受参数列表（shell=False），不接受命令字符串')
    r = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=timeout, cwd=cwd)
    if r.returncode != 0 and check:
        raise RuntimeError('CMD FAIL: %s\n%s' % (' '.join(cmd)[:200], r.stderr[-1500:]))
    return r.stderr


def under(root, *parts):
    """拼接路径并断言结果仍在 root 之下；越界立即抛错（防 ../ 穿越）。"""
    p = os.path.abspath(os.path.join(root, *parts))
    base = os.path.abspath(root)
    if os.path.commonpath([p, base]) != base:
        raise ValueError('路径越界：%s 不在 %s 之下' % (p, base))
    return p


_BLOCKED_NETS = tuple(
    ipaddress.ip_network(n) for n in (
        '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
        '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4',
        '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8'))


def _is_blocked_ip(hip):
    """显式私网/环回/链路本地/CGNAT/组播黑名单——不用 is_private，
    因为它把 198.18.0.0/15（RFC2544 基准段，代理 fake-IP 常用）也当内网，会误杀正常下载。"""
    nets = [n for n in _BLOCKED_NETS if n.version == hip.version]
    return any(hip in n for n in nets)


def https_url(url):
    """校验外部 URL：仅 https，拒绝内网 / 环回 / 链路本地地址（防 SSRF）。"""
    u = urllib.parse.urlparse(str(url))
    if u.scheme != 'https':
        raise ValueError('只允许 https 下载：%s' % url)
    host = (u.hostname or '').lower()
    if not host or host == 'localhost' or host.endswith(('.local', '.internal')):
        raise ValueError('禁止环回/内网主机：%s' % host)
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
        # 域名：解析出的每个地址都要过黑名单校验（防 DNS 指向内网）
        for info in socket.getaddrinfo(host, None):
            hip = ipaddress.ip_address(info[4][0])
            if _is_blocked_ip(hip):
                raise ValueError('域名解析到内网地址：%s -> %s' % (host, hip))
        return url
    if _is_blocked_ip(ip):
        raise ValueError('禁止内网地址下载：%s' % host)
    return url
