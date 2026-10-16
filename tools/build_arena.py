#!/usr/bin/env python3
"""Build learn/arena.html — a single self-contained page that bundles the whole
simulated training environment (lab engine + 22 scenarios + 4 timed mock exams)
together with the learning map, race calendar, cert traps and resource index.

Self-contained on purpose: the environment must work from ONE file / ONE link,
offline, with nothing else loaded.
"""
import io, os, re, datetime

ROOT = "/workspace/kc"
LAB = os.path.join(ROOT, "lab")
OUT = os.path.join(ROOT, "learn", "arena.html")


def read(p):
    return io.open(p, encoding="utf-8").read()


def js_safe(s):
    """Prevent an inline </script> inside a JS literal from closing the tag."""
    return s.replace("</script", "<\\/script").replace("<!--", "<\\!--")


css = read(os.path.join(LAB, "lab.css"))
engine = js_safe(read(os.path.join(LAB, "lab-engine.js")))
scen = js_safe(read(os.path.join(LAB, "lab-scenarios.js")))
lui = js_safe(read(os.path.join(LAB, "lab-ui.js")))
extras = js_safe(read(os.path.join(LAB, "lab-extras.js")))
comp = js_safe(read(os.path.join(LAB, "competition.js")))
compui = js_safe(read(os.path.join(LAB, "competition-ui.js")))
print("inlined: css=%d engine=%d scenarios=%d ui=%d extras=%d comp=%d compui=%d" %
      (len(css), len(engine), len(scen), len(lui), len(extras), len(comp), len(compui)))

# pull the scenario briefs + papers straight out of lab-scenarios.js so the
# landing page can never drift from what the engine actually runs
m = re.search(r"E\.SCENARIOS=SCN", scen)
assert m, "cannot locate SCENARIOS export"
block = scen[:m.start()]
titles = re.findall(r"t:'([^']+)'", block)
print("scenario briefs found:", len(titles))

TODAY = datetime.date(2026, 10, 16).isoformat()

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>云计算备赛作战台 · 一切都在这一个页面里 - 知识公社</title>
<meta name="description" content="一个页面装下全部：浏览器内虚拟服务器实训环境（22 场景自动评分）、4 套限时模拟赛、零基础六阶段学习地图、赛情赛历、认证避坑与全部资源。离线可用。">
<meta name="theme-color" content="#9e2b25">
<meta name="color-scheme" content="light">
<link rel="manifest" href="../manifest.json">
<link rel="apple-touch-icon" href="../icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="../icons/icon-192.png">
<style>
/* ---- base ---- */
:root{--red:#9e2b25;--red-dk:#7d201c;--gold:#b8873a;--blue:#2f5d8c;--green:#4c6b4f;
--ink:#2b2620;--ink2:#4a433a;--dim:#7a7167;--dim2:#9a9188;--line:#e2dbcd;--line2:#efe9dd;
--card:#fffdf8;--serif:"Songti SC","STSong","Noto Serif SC",Georgia,serif;
--fs-h1:clamp(24px,5.2vw,34px);--fs-xl:clamp(18px,3.4vw,22px);--fs-lg:16px;
--pad-x:16px;--pad-c:16px}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#f7f4ee;color:var(--ink);line-height:1.8;
font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif}
a{color:var(--red-dk)}
h1,h2,h3{margin:0 0 8px;line-height:1.35}
.topbar{background:var(--red);color:#f7efe2;font-size:12.5px;display:flex;align-items:center;gap:8px;
padding:7px 14px;font-family:var(--serif);letter-spacing:.5px}
.topbar .dot{width:7px;height:7px;background:#e8c8a0;transform:rotate(45deg);flex:none}
header.hero{background:var(--card);border-bottom:1px solid var(--line);padding:26px var(--pad-x) 22px;text-align:center}
header.hero .kicker{color:var(--red);font-size:12px;letter-spacing:5px;font-family:var(--serif)}
header.hero h1{margin:10px 0 8px;font-size:var(--fs-h1);letter-spacing:4px;font-family:var(--serif);font-weight:700}
header.hero p{margin:4px 0;color:var(--ink2);font-size:14px;max-width:640px;margin-inline:auto}
header.hero .badges{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
header.hero .badges span{border:1px solid var(--line);background:#fbf8f1;color:var(--ink2);border-radius:4px;
padding:3px 11px;font-size:12.5px;font-family:var(--serif)}
nav.tabs{position:sticky;top:0;z-index:50;background:var(--card);border-bottom:1px solid var(--line);
display:flex;overflow-x:auto;gap:2px;padding:0 8px;box-shadow:0 1px 3px rgba(64,48,24,.05)}
nav.tabs::-webkit-scrollbar{display:none}
nav.tabs a{flex:none;padding:11px 13px 9px;font-size:13.5px;color:var(--dim);border-bottom:3px solid transparent;
font-family:var(--serif);letter-spacing:1.5px;white-space:nowrap;text-decoration:none}
nav.tabs a.on{color:var(--red-dk);border-bottom-color:var(--red);font-weight:700}
.wrap{max-width:900px;margin:0 auto;padding:6px var(--pad-x) 80px}
h2.sec{font-size:var(--fs-xl);margin:30px 0 14px;font-family:var(--serif);letter-spacing:2px;font-weight:700;
display:flex;align-items:center;gap:10px}
h2.sec::before{content:"";width:9px;height:9px;background:var(--red);flex:none}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:var(--pad-c);
box-shadow:0 1px 0 rgba(64,48,24,.04);margin:10px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:620px){.grid{grid-template-columns:1fr}}
.mod{display:block;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:var(--pad-x);
text-decoration:none;color:inherit;position:relative;transition:border-color .15s,background .15s}
.mod:active{background:#fbf7ee}
.mod b{font-size:var(--fs-lg);font-family:var(--serif);letter-spacing:1px;color:var(--ink);display:block}
.mod .desc{color:var(--dim);font-size:13px;margin:6px 0 8px;line-height:1.75}
.mod .meta{font-size:12px;color:var(--dim2);font-family:var(--serif)}
.seal,.mod .ico{width:42px;height:42px;background:var(--red);color:#fdf6ea;border-radius:5px;
display:flex;align-items:center;justify-content:center;font-size:19px;font-family:var(--serif);margin-bottom:10px}
.mod.green .ico{background:var(--green)}.mod.gold .ico{background:var(--gold)}
.mod.blue .ico{background:var(--blue)}.mod.red .ico{background:var(--red)}
.list{list-style:none;margin:6px 0;padding:0}
.list li{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;
padding:9px 0;border-bottom:1px solid var(--line2)}
.list li:last-child{border-bottom:none}
.list .t{flex:1;font-size:14.5px;min-width:0}
.list .n{flex:none;color:var(--dim);font-size:12.5px;border:1px solid var(--line);border-radius:4px;
padding:2px 9px;font-family:var(--serif);white-space:nowrap}
.small{font-size:12.5px;color:var(--dim);line-height:1.8}
.goal{background:#fbf5ea;border-left:4px solid var(--gold);border-radius:0 6px 6px 0;padding:10px 14px;
font-size:13.5px;margin:12px 0}
.check{background:#f6f4ec;border:1px dashed var(--line);border-radius:6px;padding:10px 14px;
font-size:13.5px;margin:10px 0}
.note{color:var(--dim);font-size:12px;line-height:2;border-top:1px solid var(--line);margin-top:34px;
padding-top:14px;font-family:var(--serif)}
.pill{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 14px;
margin:10px 0;font-size:14px;line-height:1.9}
.lesson h3{font-size:17px;margin:26px 0 8px;color:var(--red-dk);font-family:var(--serif);letter-spacing:1px}
.lesson ul,.lesson ol{padding-left:22px;margin:6px 0}
.lesson li{margin:4px 0}
code{background:#f1ece2;padding:1px 5px;border-radius:3px;font-size:13px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#7d201c;word-break:break-all}
.cta{display:block;width:100%;padding:16px;margin:10px 0;border:none;border-radius:8px;cursor:pointer;
background:linear-gradient(150deg,#b5342c,#8e241f);color:#fff;font-size:16px;font-weight:700;
font-family:var(--serif);letter-spacing:2px;box-shadow:0 3px 10px rgba(158,43,37,.28)}
.cta:active{transform:translateY(1px)}
.cta.ghost{background:var(--card);color:var(--red-dk);border:2px solid var(--red);box-shadow:none;font-size:15px}
.cta.gold{background:linear-gradient(150deg,#c9973f,#a3762c)}
.paper{display:flex;align-items:center;gap:12px;padding:13px 14px;border:1px solid var(--line);
border-radius:6px;margin:8px 0;background:var(--card)}
.paper .pbar{flex:1;min-width:0}
.paper .pn{font-family:var(--serif);font-size:15.5px;font-weight:700;color:var(--ink)}
.paper .pd{font-size:12.5px;color:var(--dim)}
.paper .pmin{font-family:var(--serif);font-size:19px;font-weight:700;color:var(--red-dk);white-space:nowrap}
.pbtn{flex:none;border:1.5px solid var(--red);background:var(--red);color:#fdf6ea;border-radius:5px;
padding:8px 15px;font-size:13.5px;font-weight:700;cursor:pointer;font-family:var(--serif)}
.pbtn.ghost{background:var(--card);color:var(--red-dk)}
.kbd{font-family:var(--serif);border:1px solid var(--line);background:#fbf8f1;border-radius:4px;
padding:1px 7px;font-size:12.5px;white-space:nowrap}
#err{background:#7d201c;color:#fff;padding:9px 13px;border-radius:6px;margin:10px 0;font-size:13px;display:none}
</style>
<!--LAB_CSS-->
</head>
<body>
<div class="topbar"><span class="dot"></span><span>云计算备赛作战台 · 环境 / 模拟赛 / 学习地图 / 赛情 / 认证 / 视频，全在这一页里</span></div>
<header class="hero">
  <div class="kicker">ONE PAGE · EVERYTHING</div>
  <h1>云计算备赛作战台</h1>
  <p>一个页面装下全部：<b>浏览器里就能用的虚拟服务器</b>（真敲命令、真装服务、真自动评分）、<b>4 套限时模拟赛</b>、零基础六阶段学习地图、赛情赛历、认证避坑、视频与资源总入口。<b>断网也能用。</b></p>
  <div class="badges"><span>22 个实训场景</span><span>4 套限时模拟赛</span><span>自动评分</span><span>零基础路线</span><span>全离线</span></div>
</header>
<nav class="tabs">
  <a href="index.html">首页</a>
  <a class="on" href="arena.html">作战台</a>
  <a href="cloud/index.html">云赛</a>
  <a href="cloud-race.html">赛情</a>
  <a href="cloud-basics.html">基础</a>
  <a href="cloud-cert.html">认证</a>
  <a href="cloud/lab.html">实训</a>
  <a href="cloud/contest/index.html">竞赛中心</a>
  <a href="sleep.html">睡前</a>
  <a href="cloud-videos.html">视频</a>
  <a href="media/wsvideos.html">赛场</a>
  <a href="skills.html">世赛</a>
  <a href="archive.html">总目</a>
  <a href="../library.html">资源</a>
  <a href="../download.html">下载</a>
</nav>

<div class="wrap">
<div id="err"></div>

  <div class="goal"><b>两条路线，分工不同：</b>
  <a href="cloud/contest/index.html"><b>竞赛中心</b></a>是<b>真机路线</b>——7 套全真卷（国赛 / 广东 / 韩国 / 金砖 / 世赛 / 世职赛）配
  <a href="cloud/contest/env/README.md">OpenStack allinone 与 K8s 集群环境脚本</a>，要你手上有真集群，适合赛前集训；
  <b>作战台（本页）</b>是<b>零依赖路线</b>——浏览器内虚拟服务器，<b>不用装任何东西、断网可跑</b>，
  判分由函数自动判定（含世赛里昂 2024 的 52 个官方 task 编号），适合随时随地刷分与复盘。
  <b>两条不冲突，建议先作战台、再竞赛中心。</b></div>


  <button class="cta" id="goExam">🎮 直接开始模拟比赛（限时 · 自动判分 · 出报告）</button>
  <button class="cta gold" id="goComp">🏟 比赛仿真场 —— 5 场真实赛事，官方评分点判分</button>
  <button class="cta ghost" id="goLab">🧪 不限时练 —— 打开实训环境（22 个场景）</button>

  <div class="goal">这一页是<b>入口也是环境</b>。上面两个按钮点下去，<b>就在这个页面里</b>打开一个真的 Linux 终端：能敲命令、能装 Nginx、能建 MySQL、能配 DNS、能写 Ansible 剧本，写错了会给你打分，<b>不需要装任何软件、不需要联网</b>。</div>

  <section>
    <h2 class="sec">① 四套模拟赛 · 限时 · 自动判分</h2>
    <div class="card">
      <p>赛制和真赛一致：<b>倒计时、只能交一次卷、交卷出报告</b>。做完看报告就知道自己哪些评分点没拿到。</p>
      <div id="papers"></div>
      <p class="small" style="margin-top:10px">📌 第一次做建议先点「⚡ 迷你模拟」体验节奏；真正对标比赛的是「🏆 全真模拟（4 小时）」，那个是世界赛 Module 的风格。成绩、进行中的计时、每套题的最高分都存在你本机，断网也在。</p>
    </div>
  </section>

  <section>
    <h2 class="sec">② 实训环境里有什么（22 个场景，全部自动评分）</h2>
    <div class="card">
      <p class="small">环境是一台<b>真的虚拟服务器</b>：文件系统、软件包、服务、用户与权限、网络、MySQL、Docker、Ansible、LDAP、Samba 全都有。评分点是函数判定的，<b>做对得分，做错扣分，改对了立刻补分</b>。</p>
      <ul class="list" id="scnList"></ul>
      <p class="small" style="margin-top:10px">💡 每个场景里都有 <span class="kbd">📋 任务</span>（看题）· <span class="kbd">📝 文件</span>（浏览/改文件）· <span class="kbd">▶ 示范</span>（演示标准解法）· <span class="kbd">📊 评分</span>（看当前得分）。<b>卡住了先点「示范」，别死磕。</b></p>
    </div>
  </section>

  <section>
    <h2 class="sec">③ 零基础六阶段 · 按顺序走</h2>
    <div class="card">
      <p class="small">不知道从哪开始就照这个走，每阶段都带<b>过关标准</b>——达不到就别往下，硬推只会忘。</p>
      <div class="lesson">
        <h3>阶段 0 · 地基（第 1–2 周）</h3>
        <p><b>学</b>：Linux 命令、文件权限、服务管理、SSH；IP/子网/端口/DNS。<br>
        <b>读</b>：<a href="../study.html#d=tutorial_01-Linux零基础-保姆级_md">第 1 章 Linux 零基础</a> · <a href="../study.html#d=tutorial_02-网络零基础-保姆级_md">第 2 章 网络零基础</a> · <a href="courses/aws-educate.html">AWS 控制台导览（官方课件全文）</a><br>
        <b>练</b>：本页面「实训环境」里的 <b>room1 / room2 / room3</b>（机房基线、账号与目录、巡检脚本）<br>
        <b>过关</b>：不看资料，15 分钟完成一台新机的初始化 + 密钥登录 + 装 Nginx 并访问成功</p>
      </div>
      <div class="lesson">
        <h3>阶段 1 · 概念（第 3 周）</h3>
        <p><b>学</b>：IaaS/PaaS/SaaS、公有云与私有云、<b>Region 与 AZ</b>、<b>共享责任模型</b>、计费模型。<br>
        <b>读</b>：<a href="cloud-basics.html">云基础学习总纲 ① ②</a> · <a href="../study.html#d=mastery_01-疆域全景图_md">精通体系 · 疆域全景图</a><br>
        <b>过关</b>：能用自己的话讲清「为什么需要 AZ」「共享责任分界线在哪」</p>
      </div>
      <div class="lesson">
        <h3>阶段 2 · 账号与第一个服务（第 4 周）</h3>
        <p><b>学</b>：注册 AWS（<b>区域选离你最近的</b>）、<b>根用户 vs IAM</b>、建 IAM 用户与角色、开第一台 EC2。<br>
        <b>读</b>：<a href="cloud-basics.html">云基础学习总纲 ③ A · Skill Builder</a>（含只看免费内容的筛选入口）· <a href="cloud-basics.html">A2 · Ramp-Up Guides 38 份官方 PDF</a><br>
        <b>过关</b>：能用 IAM 策略限制一个用户只能读不能写</p>
      </div>
      <div class="lesson">
        <h3>阶段 3 · 核心服务（第 5–7 周）</h3>
        <p><b>读</b>：<a href="../study.html#d=tutorial_12-AWS云平台实战-保姆级_md">第 12 章 AWS 实战</a> · <a href="../study.html#d=knowledge_05-公有云核心-AWS_md">知识地图 05 公有云核心</a><br>
        <b>练</b>：<a href="cloud-basics.html">基础总纲 ⑤</a> 的六大服务五分钟实验；离线用本页面环境练 web1/web2/web3/dns1/db1/ha1/ha2<br>
        <b>过关</b>：<b>能徒手画出一张 VPC 拓扑图</b>，说清公网请求依次经过什么</p>
      </div>
      <div class="lesson">
        <h3>阶段 4 · 容器与编排（第 8–9 周）</h3>
        <p><b>读</b>：<a href="../study.html#d=tutorial_10-Docker容器入门-保姆级_md">第 10 章 Docker</a> · <a href="../study.html#d=tutorial_11-Kubernetes入门-保姆级_md">第 11 章 K8s</a> · <a href="cloud-videos.html">视频库</a>里的 CNCF 公开课<br>
        <b>练</b>：本页面环境 <b>docker1</b>（容器化部署网站）<br>
        <b>过关</b>：打镜像 → 推仓库 → Deployment 起多副本 → Service 暴露 → 删 Pod 看自动恢复</p>
      </div>
      <div class="lesson">
        <h3>阶段 5 · 自动化与可观测（第 10–11 周）</h3>
        <p><b>读</b>：<a href="../study.html#d=tutorial_13-自动化运维-保姆级_md">第 13 章 自动化运维</a> · <a href="../study.html#d=knowledge_07-自动化与IaC_md">知识地图 07 自动化与 IaC</a><br>
        <b>练</b>：本页面环境 <b>ans1</b>（Ansible 幂等）、<b>bak1</b>（备份 + 定时任务）<br>
        <b>过关</b>：自动化脚本能重复执行且结果一致（幂等）</p>
      </div>
      <div class="lesson">
        <h3>阶段 6 · 架构视野与自检（第 12 周）</h3>
        <p><b>读</b>：<a href="cloud-basics.html">基础总纲 ③ B · Well-Architected 六大支柱</a> · <a href="cloud-cert.html">云认证总库</a>（认证考纲就是官方架构观）<br>
        <b>练</b>：<a href="sleep.html">睡前考场</a>随机出题 · <a href="exam/quiz.html">学堂自测</a> · 再刷一遍本页全真模拟赛<br>
        <b>过关</b>：能指出自己环境里至少 5 条高风险项并说清改法</p>
      </div>
    </div>
  </section>

  <section>
    <h2 class="sec">④ 比赛速查 · 不知道打哪个就点「赛情」</h2>
    <div class="card">
      <ul class="list">
        <li><span class="t"><b>世赛云计算四届真相</b> —— 2019 喀山（首届）→ 2022 韩国高阳（<b>中国 IT 首金</b>）→ 2024 里昂（连冠）→ 2026 上海（<b>三连冠</b>）。<b>网上流传的「2021 佛山」「2023 东京」「2025 里昂」全部不存在</b></span><span class="n">纠错</span></li>
        <li><span class="t"><b>正在报名 / 即将开赛</b> —— 华为 ICT 第十一届（实践赛「云」<b>报名 10-31 截止</b>，省赛 11–12 月，<b>实验成绩是晋级硬门槛</b>）· 天翼云杯（上海）· 新华三杯 · 传智杯云计算大数据</span><span class="n">在报</span></li>
        <li><span class="t"><b>WSOS 2026 八项权重</b> —— 问题解决/创新 20% · 网络安全 20% · 可靠性可扩展弹性 15% · 工作组织管理 10% · 性能优化 10% · 运维考量 10% · 可持续性 10% · 沟通人际 5%</span><span class="n">权重</span></li>
        <li><span class="t"><b>排错占赛场约四分之三</b> —— 官方 TD53 明确四天赛程中两天整日排障、两天仅下午排错。<b>这是最大的提分点</b>，练排错别只练搭环境</span><span class="n">关键</span></li>
        <li><span class="t"><b>这些赛事根本不存在 / 已停办</b> —— 「全国大学生云计算技能大赛」不存在；「全国高校云计算应用创新大赛」末届 2018；KubeCon、TCon 是会议不是比赛</span><span class="n">避坑</span></li>
      </ul>
      <button class="cta ghost" onclick="location.href='cloud-race.html'" style="margin-top:12px">📅 打开赛情总台（倒计时 · 赛历 · 官方报名入口）</button>
    </div>
  </section>

  <section>
    <h2 class="sec">⑤ 认证避坑 · 照着买资料会踩的</h2>
    <div class="card">
      <ul class="list">
        <li><span class="t">❌ <b>DBS-C01 / DAS-C01 / PAS-C01</b> 还在卖 —— 2024-04 已停售；<b>MLS-C01</b> 2026-03-31 停售</span><span class="n">已停售</span></li>
        <li><span class="t">❌ <b>ACA-ECS / ACP-ECS / ACE-Cloud Architect</b> —— <b>不存在</b>。阿里云官方用 <code>aca16</code>/<code>acp01</code>/<code>ace01</code> 这种短码</span><span class="n">不存在</span></li>
        <li><span class="t">❌ 阿里云「云安全 ACP / DevOps ACP / 云网络 ACP / 云数据库 ACP」—— <b>2026-08-31 全部下线</b>，连同 17 门 Clouder 共 28 门</span><span class="n">已下线</span></li>
        <li><span class="t">❌ <b>HCSG-A</b>（华为）不存在 —— 官方前缀是 <code>HCSX</code> → HCSA/HCSP/HCSE</span><span class="n">不存在</span></li>
        <li><span class="t">❌ <b>Microsoft Learn 沙箱</b>已下线；DP-203 / AZ-204 / AI-102 已退役</span><span class="n">已退役</span></li>
        <li><span class="t">✅ <b>真正零成本的官方入口</b>：AWS Skill Builder 的 Official Practice Question Set（20 题含讲解）· 阿里云 8 门 ¥0 Clouder 认证 · 华为云微认证（完全免费）</span><span class="n">免费</span></li>
      </ul>
      <button class="cta ghost" onclick="location.href='cloud-cert.html'" style="margin-top:12px">🎓 打开云认证总库（在售清单 · 免费资源 · 零成本路径）</button>
    </div>
  </section>

  <section>
    <h2 class="sec">⑥ 全部资源入口</h2>
    <div class="card">
      <ul class="list">
        <li><span class="t"><b>零基础六阶段学习地图 + AWS 官方免费体系 + 防超费</b> → <a href="cloud-basics.html">云基础学习总纲</a>（含 Ramp-Up Guides 38 份官方 PDF 直链）</span><span class="n">先看这个</span></li>
        <li><span class="t"><b>AWS 管理控制台导览 · 官方课件全文</b>（5 节 53 张幻灯片，简体中文，已离线）→ <a href="courses/aws-educate.html">aws-educate.html</a>；<a href="courses/aws-educate-catalog.html">71 门课程库总目录</a></span><span class="n">中文</span></li>
        <li><span class="t"><b>视频课</b>（30 条 B 站链接逐条实测存活 + 失效黑名单）→ <a href="cloud-videos.html">云计算视频库</a>；世赛现场影像 → <a href="media/wsvideos.html">比赛视频馆</a></span><span class="n">视频</span></li>
        <li><span class="t"><b>碎片时间</b>：十四夜云上之城故事 + 次日清晨随机考场 → <a href="sleep.html">睡前故事考场</a>；128 道选择 → <a href="exam/quiz.html">学堂自测</a></span><span class="n">碎片</span></li>
        <li><span class="t"><b>比赛冲刺</b>：赛项分值解剖 + 四周日历 + 考场检查单 → <a href="cloud/sprint.html">30 天夺金冲刺手册</a>；224 篇真题地图 → <a href="cloud/index.html">云计算备战中心</a></span><span class="n">冲刺</span></li>
        <li><span class="t"><b>全站总目录与检索</b> → <a href="archive.html">资料总目</a> · <a href="search.html">全站检索</a> · <a href="../library.html">资源总库</a></span><span class="n">导航</span></li>
      </ul>
    </div>
  </section>

  <p class="note">本页环境由站内模拟实训引擎驱动（<code>lab/lab-engine.js</code> 虚拟服务器 + <code>lab-scenarios.js</code> 22 场景与 4 套试卷 + <code>lab/lab-ui.js</code> 界面），已全量验证：<b>57 项冒烟测试全过，22 个场景均满足「初始分 &lt; 100、示范解法 = 100%」</b>。本页为单文件自包含，<b>断网可用</b>，所有成绩与进度保存在本机浏览器，不上传。<br>页面内容核实基准日 2026-10-16；认证与赛事信息以各厂商/主办方官网当日口径为准。</p>
</div>

<!-- ============ 实战中心（模拟赛 + 场景入口） ============ -->
<div id="labView">
  <div class="topbar"><span class="dot"></span><span id="labTitle">云计算作战台</span>
    <span style="margin-left:auto"></span>
    <button class="pbtn ghost" onclick="closeLab()">✕ 退出</button>
  </div>
  <div class="wrap" id="labBody" style="padding-top:14px"></div>
</div>

<!-- ============ 终端 ============ -->
<div id="termView">
  <div class="tv-head">
    <button class="tv-btn" id="tvBack">← 返回</button>
    <div class="tv-title" id="tvTitle">模拟实训</div>
    <div id="tvScore" style="font-size:11px;color:#8b949e;margin-right:2px"></div>
    <button class="tv-btn" id="tvGradeBtn">📊 评分</button>
  </div>
  <div class="tv-scr" id="tvScr"></div>
  <div class="tv-pad">
    <div class="tv-chips" id="tvChips"></div>
    <div class="tv-inrow">
      <button class="tv-mini" id="tvHUp">⌃</button>
      <button class="tv-mini" id="tvHDn">⌄</button>
      <input id="tvIn" placeholder="输入命令，回车执行" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="go">
      <button class="tv-run" id="tvRun">▶</button>
    </div>
    <div class="tv-tools">
      <button class="tv-mini" id="tvBriefBtn">📋 任务</button>
      <button class="tv-mini" id="tvFilesBtn">📝 文件</button>
      <button class="tv-mini" id="tvDemoBtn">▶ 示范</button>
      <button class="tv-mini" id="tvResetBtn">↺ 重开</button>
    </div>
  </div>
  <div class="tv-panel" id="tvPanel"></div>
</div>

<div id="tvEdit">
  <div class="tv-edit-card">
    <div class="tv-edit-head"><span id="tvEditPath">file</span><button class="tv-btn" id="tvEditClose">✕</button></div>
    <textarea id="tvEditArea" spellcheck="false"></textarea>
    <div class="tv-edit-foot"><button class="tv-btn" id="tvEditCancel">取消</button><button class="tv-btn primary" id="tvEditSave">💾 保存</button></div>
  </div>
</div>
<div id="tvToast"></div>
<div id="tvConfirm"><div class="tv-edit-card sm"><div id="tvConfirmMsg"></div>
  <div class="tv-edit-foot"><button class="tv-btn" id="tvConfirmNo">取消</button><button class="tv-btn primary" id="tvConfirmYes">确定</button></div></div></div>

<script>/*LAB_ENGINE*/</script>
<script>/*LAB_EXTRAS*/</script>
<script>/*LAB_SCENARIOS*/</script>
<script>
/* ---- 主页面钩子：lab-ui 需要的最小实现 ---- */
window.renderLabCenter=function(){};
window.openLabCenter=function(){ document.getElementById('labView').classList.add('on'); renderLabCenter(); };
window.closeLab=function(){
  document.getElementById('labView').classList.remove('on');
  document.getElementById('termView').classList.remove('on');
};
window.startSim=function(id){ try{ window.LabUI.startExam(id); }catch(e){ showErr(e); } };
</script>
<script>/*LAB_UI*/</script>
<script>/*LAB_COMPETITION*/</script>
<script>/*LAB_COMPETITION_UI*/</script>
<script>
(function(){
'use strict';
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function showErr(e){ var b=document.getElementById('err'); b.style.display='block';
  b.textContent='引擎异常：'+(e&&e.message||e)+'　（若反复出现请用浏览器打开 F12 看控制台）'; }

/* ---- 启动健康检查 ---- */
var E=window.LabEngine;
if(!E||!E.SCENARIOS){ showErr('LabEngine 未加载'); return; }

var SCN=E.SCENARIOS, PAPERS=E.EXAM_PAPERS||[];

/* 渲染四套试卷 */
var ph=document.getElementById('papers');
ph.innerHTML=PAPERS.map(function(p){
  var mins=p.dur>=60? Math.round(p.dur/60)+' 小时' : p.dur+' 分钟';
  return '<div class="paper"><div class="pbar"><div class="pn">'+esc(p.t)+'</div>'+
    '<div class="pd">'+esc(p.desc||'')+' · '+p.ids.length+' 个任务</div></div>'+
    '<div class="pmin">'+mins+'</div>'+
    '<button class="pbtn" data-exam="'+p.id+'">开考</button></div>';
}).join('') || '<p class="small">未读到试卷定义</p>';
ph.addEventListener('click',function(e){
  var b=e.target.closest('[data-exam]'); if(!b) return;
  try{ window.LabUI.startExam(b.getAttribute('data-exam')); }
  catch(err){ showErr(err); }
});

/* 渲染 22 个场景 */
var sl=document.getElementById('scnList');
sl.innerHTML=SCN.map(function(s){
  var tag=(s.exam&&s.exam.length)? s.exam.map(function(x){return x.toUpperCase();}).join(' ') : '练习';
  return '<li><span class="t">'+esc(s.t||s.id)+'<br><span class="small">'+
    esc((s.brief||'').slice(0,52))+'…</span></span>'+
    '<span class="n">'+tag+'</span>'+
    '<span class="n" style="border-color:#9e2b25;color:#9e2b25;cursor:pointer" data-scn="'+s.id+'">进入</span></li>';
}).join('');
sl.addEventListener('click',function(e){
  var b=e.target.closest('[data-scn]'); if(!b) return;
  try{ window.LabUI.openScenario(b.getAttribute('data-scn')); }
  catch(err){ showErr(err); }
});

/* 比赛仿真场 */
document.getElementById("goComp").addEventListener("click", function () {
  try {
    document.getElementById("labView").classList.add("on");
    window.CompUI.open();
  } catch (e) { showErr(e); }
});

/* 两个大按钮 */
document.getElementById('goExam').addEventListener('click',function(){
  try{ window.LabUI.startExam('mini'); }catch(e){ showErr(e); }
});
document.getElementById('goLab').addEventListener('click',function(){
  try{ window.LabUI.openScenario(SCN[0].id); }catch(e){ showErr(e); }
});

/* 确保 hook 转发到我们的实现 */
window.openLabCenter=window.openLabCenter||function(){ renderLabCenter(); };
})();
</script>
</body>
</html>
"""

out = (HTML.replace("<!--LAB_CSS-->", css)
           .replace("/*LAB_ENGINE*/", engine)
           .replace("/*LAB_SCENARIOS*/", scen)
           .replace("/*LAB_UI*/", lui)
           .replace("/*LAB_EXTRAS*/", extras)
           .replace("/*LAB_COMPETITION*/", comp)
           .replace("/*LAB_COMPETITION_UI*/", compui))

io.open(OUT, "w", encoding="utf-8").write(out)
print("wrote %s  (%.1f KB)" % (OUT, len(out) / 1024))
