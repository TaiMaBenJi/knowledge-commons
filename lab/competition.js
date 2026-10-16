/* =====================================================================
   competition.js · 云计算竞赛仿真场
   ------------------------------------------------------------
   对标真实赛事：赛项模块结构、官方评分任务编号、权重与赛程均取自
   公开的官方评分脚本与技术描述（里昂 2024 Skill 39、上海 2026 Skill 53、
   河南省第46届世赛选拔赛技术文件、金砖云计算赛项）。
   任务编号 task_A01_01 等为官方评分脚本原始标识，便于与原版核对。

   依赖：lab-engine.js + lab-extras.js + lab-scenarios.js
   浏览器 / Node 双兼容。
   ===================================================================== */
(function(root){
'use strict';
var E=root.LabEngine;
if(!E) return;
var X=E.extras||{};

function T(s){ return String(s||''); }
function R(vm,p){ var s=vm.read(p); return s===null?'':String(s); }
function has(vm,p){ return vm.read(p)!==null; }
function svcOn(vm,n){ var s=vm.svcs[n]; return !!(vm.pkgs[n==='smbd'?'samba':n]||vm.pkgs[n]) && !!(s&&s.running); }
function installed(vm,n){ var s=vm.svcs[n]; return !!((vm.pkgs[n]||vm.pkgs[n+'-server'])&&s&&s.installed); }
function rx(s,re){ return re.test(T(s)); }
function dnsA(vm,name){ var r=E.dnsLookup(vm,name,'A'); return r.status==='NOERROR'?r.value:null; }
function f(v,m){ return {ok:!!v, msg:m||(v?'':'未达标')}; }

/* ================= 通用检查原语 ================= */
/**
 * 记录声明检查（静态）。
 * 仿真器的 DNS 解析只实现了 A 与 PTR；SRV/AAAA/CNAME 这类记录在真实评分脚本里
 * 通常也是查区域文件声明，因此这里按「配置里是否真的声明了该记录」判定，
 * 避免出现永远拿不到的死分。
 */
var ZONEFILES=['/etc/bind/db.paris.local','/etc/bind/named.conf.local','/etc/dnsmasq.conf',
               '/etc/bind/db.10.168.192.in-addr.arpa','/etc/bind/db.10.168.192.ip6.arpa'];
function zoneText(vm){
  var out=[];
  ZONEFILES.forEach(function(p){ var s=R(vm,p); if(s) out.push('### '+p+'\n'+s); });
  return out.join('\n');
}
function escRe(s){ return String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
function recDecl(vm,name,type){
  var z=zoneText(vm), n=escRe(name);
  /* bind 区域文件行格式：名称 [TTL] [类] 类型 数据  —— 中间的类与类型必须允许出现 */
  var head='^\\s*'+n+'\\b[^\\n]*?';
  if(type==='A'){
    return new RegExp(head+'\\bA\\b\\s+(?:\\d{1,3}\\.){3}\\d{1,3}\\b','mi').test(z)
        || new RegExp('^\\s*address=/'+n+'/','m').test(z)
        || new RegExp('^\\s*host-record='+n+',','m').test(z);
  }
  if(type==='AAAA'){
    return new RegExp(head+'\\bAAAA\\b\\s+[0-9A-Fa-f]*:[0-9A-Fa-f:]*','mi').test(z);
  }
  if(type==='CNAME'){
    return new RegExp(head+'\\bCNAME\\b\\s+\\S+','mi').test(z);
  }
  if(type==='SRV'){
    return new RegExp('^\\s*_[^\\s.]+\\._[^\\s.]*\\.'+n+'\\b[^\\n]*\\bSRV\\b','mi').test(z)
        || new RegExp(head+'\\bSRV\\b\\s+\\S+','mi').test(z);
  }
  return false;
}
/** A 记录：实时解析到、或区域文件里声明了，都算达标（与真实评分脚本的两种查法一致） */
function aOK(vm,name,ip){
  var v=dnsA(vm,name);
  if(v && (!ip || v===ip)) return true;
  return recDecl(vm,name,'A') && (!ip || new RegExp(escRe(name)+'\\s+(?:\\d{1,3}\\.){3}\\d{1,3}\\b').test(zoneText(vm)));
}

var CK={
  running:function(vm,n,pkg){ return {ok:installed(vm,n)&&vm.svcs[n]&&vm.svcs[n].running, msg:'服务 '+n+' 未安装或在运行中'}; },
  file:function(vm,p,re,label){ var c=R(vm,p); return {ok:!!c&&(!re||re.test(c)), msg:(c?'':'缺少文件 ')+(label||p)}; },
  conf:function(vm,p,re,label){ var c=R(vm,p); return {ok:!!c&&re.test(c), msg:c?'配置不满足：'+(label||re.source||''):'缺少配置 '+p}; },
  dns:function(vm,name,ip){ var v=dnsA(vm,name); return {ok:v===ip, msg:(v||'NXDOMAIN')+' ≠ '+ip}; }
};

/* =====================================================================
   一、世赛云计算 · 里昂 2024（Skill 39）
   Module A（Linux）16 个评分点 / 52 个官方任务编号
   ===================================================================== */
var LYON24_A=[
 {id:'A01', t:'LDAP 目录服务', tasks:[
   {id:'task_A01_01', d:'OU（组织单位）Employees 存在', p:4, f:function(vm){
     return {ok:vm.ldapE.some(function(e){return /ou=employees/i.test(e.dn);}), msg:'目录里没有 ou=employees'}; }},
   {id:'task_A01_02', d:'检查用户 jamie、peter、admin 是否存在', p:6, f:function(vm){
     var need=['jamie','peter','admin'], miss=need.filter(function(u){return !vm.users[u];});
     return {ok:miss.length===0, msg:miss.length?('缺用户：'+miss.join('、')):''}; }},
   {id:'task_A01_03', d:'检查 jamie 与 peter 的用户属性（attributes）是否正确', p:5, f:function(vm){
     var j=vm.users['jamie'],p=vm.users['peter'];
     return {ok:!!(j&&p&&j.shell&&p.shell), msg:'用户属性未设置（usermod -s /bin/bash 等）'}; }},
   {id:'task_A01_04', d:'检查 LDAP 用户能否登录', p:5, f:function(vm){
     var n=vm.ldapE.filter(function(e){return /uid=jamie/i.test(e.dn);}).length;
     return {ok:n>0, msg:'jamie 未导入 LDAP 目录'}; }}
 ]},
 {id:'A02', t:'证书体系（Root CA / Services CA）', tasks:[
   {id:'task_A02_01', d:'Root CA（根证书）检查', p:5, f:function(vm){
     var c=[R(vm,'/etc/ssl/ca/root.crt'),R(vm,'/etc/ssl/certs/root.crt'),R(vm,'/root/ca/root.crt')].join('');
     return {ok:/BEGIN CERTIFICATE/.test(c)&&/CA:TRUE/.test(c), msg:'缺少带 CA:TRUE 的根证书'}; }},
   {id:'task_A02_02', d:'Services CA（服务证书）检查', p:5, f:function(vm){
     var c=[R(vm,'/etc/ssl/ca/services.crt'),R(vm,'/etc/ssl/certs/services.crt')].join('');
     return {ok:/BEGIN CERTIFICATE/.test(c), msg:'缺少 Services CA 证书'}; }},
   {id:'task_A02_03', d:'Web 服务器证书检查', p:4, f:function(vm){
     var c=[R(vm,'/etc/ssl/certs/web.crt'),R(vm,'/etc/nginx/ssl/web.crt')].join('');
     return {ok:/BEGIN CERTIFICATE/.test(c), msg:'缺少 Web 服务器证书'}; }},
   {id:'task_A02_04', d:'邮件服务器证书检查', p:4, f:function(vm){
     var c=[R(vm,'/etc/ssl/certs/mail.crt'),R(vm,'/etc/postfix/ssl/mail.crt')].join('');
     return {ok:/BEGIN CERTIFICATE/.test(c), msg:'缺少邮件服务器证书'}; }}
 ]},
 {id:'A03', t:'Samba 共享与访客控制', tasks:[
   {id:'task_A03_01', d:'Samba 用户检查', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:!!c&&!!vm.users['jamie'], msg:'未配置 Samba 或缺少用户'}; }},
   {id:'task_A03_02', d:'匿名访问 public 共享（应失败）', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:/\[public\][\s\S]*?guest ok\s*=\s*no/i.test(c), msg:'public 共享未禁止访客，匿名读不应成功'}; }},
   {id:'task_A03_03', d:'用户身份在 public 共享写入（应成功）', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:/\[public\][\s\S]*?read only\s*=\s*no/i.test(c), msg:'public 共享未开放写入'}; }},
   {id:'task_A03_04', d:'匿名在 public 共享写入（应失败）', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:/\[public\][\s\S]*?guest ok\s*=\s*no/i.test(c)&&/\[public\][\s\S]*?read only\s*=\s*no/i.test(c), msg:'匿名写入未被正确禁止'}; }},
   {id:'task_A03_05', d:'匿名访问 internal 共享（应失败）', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:/\[internal\][\s\S]*?guest ok\s*=\s*no/i.test(c), msg:'internal 共享未禁止访客'}; }},
   {id:'task_A03_06', d:'用户身份在 internal 共享写入（应成功）', p:4, f:function(vm){
     var c=R(vm,'/etc/samba/smb.conf');
     return {ok:/\[internal\][\s\S]*?read only\s*=\s*no/i.test(c), msg:'internal 共享未开放写入'}; }}
 ]},
 {id:'A04', t:'DNS 正向 / SRV / 递归 / 反向区', tasks:[
   {id:'task_A04_01', d:'int-srv01 的 A 记录检查', p:5, f:function(vm){
     var v=dnsA(vm,'int-srv01');
     return {ok:aOK(vm,'int-srv01')&&(!v||/^192\.168\.10\.(20|21)$/.test(v)),
             msg:(v?('解析到 '+v):'区域文件里也未声明 int-srv01 的 A 记录')}; }},
   {id:'task_A04_02', d:'int-srv01 的 SRV 记录检查', p:5, f:function(vm){
     return {ok:recDecl(vm,'int-srv01','SRV'), msg:'区域文件里没有 int-srv01 的 SRV 记录声明'}; }},
   {id:'task_A04_03', d:'递归解析器（Recurse resolver）检查', p:5, f:function(vm){
     var c=R(vm,'/etc/bind/bind9.conf')+R(vm,'/etc/bind/named.conf.options')+R(vm,'/etc/bind/named.conf.local')+R(vm,'/etc/dnsmasq.conf');
     return {ok:/recursion\s+yes|recursion/.test(c), msg:'未在任何 bind 配置中开启 recursion yes'}; }},
   {id:'task_A04_04', d:'从服务器（Slave server）检查', p:4, f:function(vm){
     var c=R(vm,'/etc/bind/named.conf.local')+R(vm,'/etc/bind/db.paris.local');
     return {ok:/type\s+(slave|secondary)|masters\s*\{[^}]*\S/.test(c), msg:'未配置 slave/secondary 区或 masters 语句'}; }},
   {id:'task_A04_05', d:'v4 与 v6 反向区的从服务器检查', p:4, f:function(vm){
     var v4=R(vm,'/etc/bind/db.10.168.192.in-addr.arpa'), v6=R(vm,'/etc/bind/db.10.168.192.ip6.arpa');
     var lv4=/type\s+(slave|secondary)|masters\s*\{[^}]*\S/.test(R(vm,'/etc/bind/named.conf.local'))&&/\S/.test(v4.replace(/^\s*#.*$/gm,'').trim());
     var lv6=/\S/.test(v6.replace(/^\s*#.*$/gm,'').trim());
     return {ok:lv4&&lv6, msg:'反向区：v4='+(lv4?'有':'缺')+' v6='+(lv6?'有':'缺')}; }}
 ]},
 {id:'A05', t:'IPv4 / IPv6 转发', tasks:[
   {id:'task_A05_01', d:'IPv4 与 IPv6 转发（forwarding）已启用检查', p:8, f:function(vm){
     var v4=X.forwarding4?X.forwarding4(vm):false, v6=X.forwarding6?X.forwarding6(vm):false;
     return {ok:v4&&v6, msg:'v4='+v4+' v6='+v6+'（需 sysctl -w 并写盘）'}; }}
 ]},
 {id:'A06', t:'SNAT 源地址转换', tasks:[
   {id:'task_A06_01', d:'SNAT（源地址转换）检查', p:8, f:function(vm){
     return {ok:!!(X.hasNat&&X.hasNat(vm)), msg:'POSTROUTING 链缺少 MASQUERADE / SNAT'}; }}
 ]},
 {id:'A07', t:'WireGuard 站点互联', tasks:[
   {id:'task_A07_01', d:'WireGuard 接口检查', p:5, f:function(vm){
     var w=X.wg?X.wg(vm):{exists:false};
     return {ok:!!w.exists&&/Address/.test(R(vm,'/etc/wireguard/wg0.conf')), msg:'缺少 /etc/wireguard/wg0.conf'}; }},
   {id:'task_A07_02', d:'wg0 是否配置了 PSK（预共享密钥）', p:5, f:function(vm){
     return {ok:!!(X.wgHasPSK&&X.wgHasPSK(vm)), msg:'Peer 段缺少 PresharedKey'}; }}
 ]},
 {id:'A08', t:'透明代理', tasks:[
   {id:'task_A08_01', d:'透明代理（transparent proxy）检查', p:8, f:function(vm){
     var c=R(vm,'/etc/squid/squid.conf');
     var cc=c.replace(/^\s*#.*$/gm,'');
     var okc=/\bintercept\b/.test(cc)&&/^\s*acl\s+\S+\s+(SRC|DST)\b/m.test(cc);
     return {ok:okc, msg:'squid.conf 缺少 intercept 模式或对应 ACL'}; }}
 ]},
 {id:'A09', t:'邮件服务', tasks:[
   {id:'task_A09_01', d:'以 jamie 身份发邮件', p:5, f:function(vm){
     var q=X.mailq?X.mailq(vm):[];
     return {ok:q.some(function(m){return /jamie/i.test(T(m.from));}), msg:'队列中没有以 jamie 身份投递的邮件'}; }},
   {id:'task_A09_02', d:'echo 服务测试', p:5, f:function(vm){
     var c=R(vm,'/etc/postfix/main.cf');
     return {ok:/^mydomain|^myhostname|^\s*myorigin/m.test(c), msg:'postfix 未正确配置域名'}; }}
 ]},
 {id:'A10', t:'自动挂载与备份', tasks:[
   {id:'task_A10_01', d:'fstab（自动挂载配置）检查', p:5, f:function(vm){
     var c=R(vm,'/etc/fstab');
     return {ok:/\S+\s+\S+\s+(ext4|xfs|btrfs)\s+\S+\s+[0-9]\s+[0-9]/.test(c), msg:'fstab 中没有合法挂载项'}; }},
   {id:'task_A10_02', d:'备份脚本检查', p:5, f:function(vm){
     var c=R(vm,'/root/backup.sh');
     var cr=R(vm,'/var/spool/cron/crontabs/root');
     var hasScript=/backup/.test(c)&&/\S/.test(c);
     var hasCron=/backup\.sh|backup/.test(cr.replace(/^\s*#.*$/gm,''));
     return {ok:hasScript&&hasCron,
             msg:'脚本'+(hasScript?'有':'缺')+' · crontab '+(hasCron?'已挂定时':'未挂定时')}; }}
 ]},
 {id:'A11', t:'SSH 证书认证', tasks:[
   {id:'task_A11_01', d:'是否设置 TrustedUserCAKeys 选项', p:5, f:function(vm){
     var c=R(vm,'/etc/ssh/sshd_config');
     return {ok:/^\s*TrustedUserCAKeys\s+\S+/m.test(c), msg:'sshd_config 缺少 TrustedUserCAKeys'}; }},
   {id:'task_A11_02', d:'SSH 证书认证（ssh cert auth）检查', p:5, f:function(vm){
     var c=R(vm,'/etc/ssh/sshd_config');
     return {ok:/^\s*TrustedUserCAKeys\s+\S+/m.test(c)&&/^\s*PubkeyAuth\s+yes/m.test(c), msg:'未启用基于证书的公钥认证'}; }}
 ]},
 {id:'A12', t:'HAProxy 反向代理与高可用', tasks:[
   {id:'task_A12_01', d:'反向代理是否监听 80 端口', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/(bind\s+[^\n:]*:80|bind\s+\*?:\s*80)/.test(c), msg:'未绑定 80'}; }},
   {id:'task_A12_02', d:'反向代理是否监听 443 端口', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/bind\s+[^\n:]*:443/.test(c), msg:'未绑定 443'}; }},
   {id:'task_A12_03', d:'反向代理是否在做负载均衡', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/^\s*server\s+\S+\s+\S+:\d+/m.test(c), msg:'backend 下没有 server'}; }},
   {id:'task_A12_04', d:'haproxy 是否设置了指定头部（header）', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/http-request\s+(set-header|add-header)|http-response\s+(set-header|add-header)/.test(c), msg:'缺少 http-request/set-header'}; }},
   {id:'task_A12_05', d:'HTTPS 跳转（HTTP→HTTPS）检查', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/redirect\s+scheme\s+https/.test(c), msg:'缺少 redirect scheme https'}; }},
   {id:'task_A12_06', d:'HTTPS 证书检查', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/\bssl\b|\bcrt\b|ca-file|ca_base_dir|verify\s+(required|optional)/.test(c), msg:'frontend 未配置 ssl/crt/verify'}; }},
   {id:'task_A12_07', d:'VIP（虚拟 IP）是否接收 Web 流量', p:4, f:function(vm){
     var c=R(vm,'/etc/keepalived/keepalived.conf');
     return {ok:/virtual_ipaddress/.test(c), msg:'keepalived 未配置 virtual_ipaddress'}; }}
 ]},
 {id:'A13', t:'DNS 区域记录（mail / VRRP / AAAA / CNAME）', tasks:[
   {id:'task_A13_01', d:'DNS 区（zone）检查', p:4, f:function(vm){
     /* 必须是真的区域定义：bind zone 文件要有 $TTL / @ IN SOA，dnsmasq 要有 address= 条目 */
     var z=R(vm,'/etc/bind/db.paris.local')+R(vm,'/etc/bind/named.conf.local');
     var q=R(vm,'/etc/dnsmasq.conf');
     var okZone=/\$TTL|@\s+IN\s+SOA|zone\s+"paris\.local"/.test(z);
     var okQ=/^\s*address=\//m.test(q);
     return {ok:okZone||okQ, msg:okZone?'bind zone 已定义':(okQ?'dnsmasq address 条目已配置':'未建立区域定义（需要 zone 文件 $TTL/@ IN SOA 或 dnsmasq address=）')}; }},
   {id:'task_A13_02', d:'递归解析器检查', p:4, f:function(vm){
     var c=R(vm,'/etc/bind/named.conf.options')+R(vm,'/etc/bind/bind9.conf');
     return {ok:/recursion\s+yes|recursion/.test(c), msg:'未开启 recursion'}; }},
   {id:'task_A13_03', d:'mail 的 A 记录检查', p:4, f:function(vm){
     return {ok:aOK(vm,'mail'), msg:'mail 既解析不到、区域文件里也没声明'}; }},
   {id:'task_A13_04', d:'prx-vrrp 的 A 记录检查', p:4, f:function(vm){
     return {ok:aOK(vm,'prx-vrrp'), msg:'prx-vrrp 既解析不到、区域文件里也没声明'}; }},
   {id:'task_A13_05', d:'mail 的 AAAA 记录检查', p:4, f:function(vm){
     return {ok:recDecl(vm,'mail','AAAA'), msg:'区域文件里没有 mail 的 AAAA 记录'}; }},
   {id:'task_A13_06', d:'web 的 CNAME 记录检查', p:4, f:function(vm){
     return {ok:recDecl(vm,'web','CNAME'), msg:'区域文件里没有 web 的 CNAME 记录'}; }}
 ]},
 {id:'A14', t:'Web 内容与自定义错误页', tasks:[
   {id:'task_A14_01', d:'main.html 可被访问', p:6, f:function(vm){
     var h=R(vm,'/var/www/html/main.html');
     var okh=/\S/.test(h)&&!/Welcome to nginx/.test(h);
     /* main.html 存在即算；nginx 若把 index 指向 main.html 更好 */
     return {ok:okh, msg:h?(okh?'':'main.html 仍是 nginx 默认页'):'缺少 /var/www/html/main.html'}; }},
   {id:'task_A14_02', d:'404.html 可被访问', p:6, f:function(vm){
     return {ok:/\S/.test(R(vm,'/var/www/html/404.html')), msg:'缺少 404.html'}; }}
 ]},
 {id:'A15', t:'Ansible 自动化', tasks:[
   {id:'task_A15_01', d:'ansible ping（连通性）检查', p:6, f:function(vm){
     var c=R(vm,'/etc/ansible/hosts');
     return {ok:/\[/.test(c), msg:'inventory 未配置'}; }},
   {id:'task_A15_02', d:'main.html 可被访问', p:6, f:function(vm){
     var y=R(vm,'/root/play.yml')+R(vm,'/root/site.yml');
     return {ok:/copy:/.test(y)&&/main\.html/.test(y), msg:'playbook 未包含分发 main.html 的任务'}; }}
 ]},
 {id:'A16', t:'端到端连通性（端口转发与转发链）', tasks:[
   {id:'task_A16_01', d:'udp/53 端口转发检查', p:4, f:function(vm){
     return {ok:!!(X.hasPreroute&&X.hasPreroute(vm))||/53/.test(R(vm,'/etc/haproxy/haproxy.cfg')), msg:'缺少 53 端口转发'}; }},
   {id:'task_A16_02', d:'tcp/80 与 443 端口转发检查', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg');
     return {ok:/:\s*80|:80\b/.test(c)&&/:\s*443|:443\b/.test(c), msg:'缺少 80/443 转发'}; }},
   {id:'task_A16_03', d:'143 端口 STARTTLS 检查', p:4, f:function(vm){
     var c=R(vm,'/etc/haproxy/haproxy.cfg')+R(vm,'/etc/postfix/main.cf');
     return {ok:/starttls|587|:143/.test(c), msg:'未配置 143/STARTTLS'}; }},
   {id:'task_A16_04', d:'IPv4 与 IPv6 可用性检查', p:4, f:function(vm){
     return {ok:!!(X.forwarding4&&X.forwarding4(vm))&&!!(X.forwarding6&&X.forwarding6(vm)), msg:'转发未全开'}; }},
   {id:'task_A16_05', d:'端到端（End-to-End）测试', p:4, f:function(vm){
     var s=vm.svcs['haproxy'], c=R(vm,'/etc/haproxy/haproxy.cfg');
     var on=!!(s&&s.running&&!s.failed), back=/^\s*server\s+\S+\s+\S+:\d+/m.test(c);
     var fwd=X.forwarding4?X.forwarding4(vm):false;
     return {ok:on&&back&&fwd,
             msg:'HAProxy '+(on?'已运行':'未运行/启动失败')+' · 后端'+(back?'已配置':'缺失')+' · 转发'+(fwd?'已开':'未开')}; }}
 ]}
];

/* Module B · Windows（从官方评分 PowerShell 脚本提取的逐主机检查项） */
var LYON24_B=[
 {id:'DC1', t:'域控 1 dc1.paris.local', items:[
   '主机名与 IP 地址','ADDS：DC 已安装并配置','ADDS：用户按正确的 OU 创建','ADDS：用户加入对应组',
   'ADDS：使用自动化 PowerShell 脚本创建用户','ADDS：为 HR 部门设置细粒度密码策略',
   'DNS：paris.local 正向区','DNS：paris.local 反向区','GPO：登录消息横幅','GPO：设置环境变量 Name=TheErasTour、Value=2024',
   'GPO：禁用本地 Administrator 账户','GPO：阻止 LM 哈希存入本地 SAM 与 AD','GPO：每周五 13:00 检查 Windows 更新',
   'GPO：SALES、MKT、HR 用户不得访问注册表','GPO：SALES、MKT、HR 不能运行 powershell.exe / cmd.exe',
   'GPO：关闭 SALES、MKT、HR 的文件历史记录','GPO：Tech 组登录时自动启动 powershell.exe']},
 {id:'DC2', t:'域控 2 dc2.lyon.paris.local', items:[
   '主机名与 IP 地址','ADDS：DC2 为子域 lyon.paris.local','ADDS：remote1-20 用户已创建','ADDS：REMOTE 安全组已创建']},
 {id:'FILE-SRV', t:'文件服务器 file-srv.paris.local', items:[
   '主机名与 IP 地址','已加入域','RemoteApp（远程应用）','DFS：\\\\paris.local\\CSDrive\\Common 共享已配置',
   'DFS：MKT 挂载目录已配置','DFS：SALES 挂载目录已配置','DFS：HR 挂载目录已配置','DFS：TECH 挂载目录已配置',
   'DFS：个人共享（配额 Quota）','DFS：个人共享（可执行文件限制）','DFS 复制（DFS Replication）']},
 {id:'LA-ROUTER', t:'路由器 LA-Router', items:['主机名与 IP 地址','DNS：paris.com 区','RRAS：路由服务已安装并配置']},
 {id:'LYON-ROUTER', t:'路由器 lyon-router.lyon.paris.local', items:[
   '主机名与 IP 地址','已加入域','站点到站点 VPN：Paris 与 Lyon 之间连通',
   'DHCP：租约范围、DNS 服务器、网关、作用域名称、租约时长','DHCP：排除范围（Exclusion）']},
 {id:'NW-SRV', t:'网络服务器 nw-srv.paris.local', items:[
   '主机名与 IP 地址','已加入域','DNS：从主 DNS 传输的辅助区（Secondary Zone transfer）',
   'DHCP：租约范围、DNS 服务器、网关、作用域名称、租约时长','DHCP：排除范围（Exclusion）']},
 {id:'PARIS-ROUTER', t:'路由器 paris-router.paris.local', items:[
   '主机名与 IP 地址','已加入域','反向代理：PARIS-Router 已配置为反向代理','RRAS：DHCP 中继代理（DHCP Relay Agent）']},
 {id:'WEB-SRV', t:'Web 服务器 web-srv.paris.local', items:[
   '主机名与 IP 地址','已加入域','CA：paris.local 的根 CA','CA：证书注册（Certificate Enrollment）',
   'CA：主题备用名称（Subject Alternative Name）','IIS：已在 WEB-SRV 上安装','IIS：虚拟主机（Virtual Hosts）',
   'IIS：通过 HTTPS 访问无证书错误']}
];

/* WSOS 2026 八项权重（官方职业标准） */
var WSOS2026=[
 {k:'问题解决、创新与创造力', w:20, note:'设计分层架构、排障、迁移方案'},
 {k:'网络安全', w:20, note:'认证授权、加密传输、安全组与基线'},
 {k:'可靠性、可扩展性与弹性', w:15, note:'高可用、负载均衡、弹性伸缩'},
 {k:'工作组织与管理', w:10, note:'读题拆解、交付顺序、时间管理'},
 {k:'性能与优化', w:10, note:'资源规格、监控、瓶颈定位'},
 {k:'运营考量', w:10, note:'变更、可观测、事故响应'},
 {k:'可持续性', w:10, note:'资源利用率、环境影响、能耗'},
 {k:'沟通与人际交往', w:5, note:'交付文档写得清楚本身就是分'}
];

/* ================= 赛事定义 ================= */
var COMPS={};

COMPS['ws-lyon24']={
 id:'ws-lyon24', name:'世赛云计算 · 里昂 2024（Skill 39）',
 sub:'真实赛制还原：Module A 共 16 个评分点 / 52 个官方任务编号 + Module B 八台主机清单',
 days:4, totalMin:360, level:'世界赛',
 notes:[
  'Module A · Linux：16 个评分点，52 个官方 task 编号（A01–A16）',
  'Module B · Windows：8 台主机的逐项检查（DC1/DC2/FILE-SRV/LA-ROUTER/LYON-ROUTER/NW-SRV/PARIS-ROUTER/WEB-SRV）',
  'Module D：故障排除（工单 + 拓扑），官方在 2024 届从 6 小时 12 题压缩为 3 小时 12 题、难度提升',
  '第 4 天为组队任务 + 英文演讲（不计分）'
 ],
 modules:[
  {id:'A', name:'Module A · Linux', w:60, mins:180, groups:LYON24_A},
  {id:'B', name:'Module B · Windows', w:30, mins:120, hosts:LYON24_B},
  {id:'D', name:'Module D · 故障排除', w:10, mins:60,
   groups:[{id:'D01', t:'排障特训（3 个急诊任务）', tasks:[
     {id:'task_D01_01', d:'fix1 · nginx 服务起不来', p:30, scn:'fix1'},
     {id:'task_D01_02', d:'fix2 · 磁盘爆满', p:35, scn:'fix2'},
     {id:'task_D01_03', d:'fix3 · 403 权限', p:35, scn:'fix3'}
   ]}]}
 ],
 wsos:WSOS2026
};

COMPS['ws-shanghai26']={
 id:'ws-shanghai26', name:'世赛云计算 · 上海 2026（Skill 53）',
 sub:'中国首次主办 · 赛程 3.5 天 / 22 小时 · 公有云平台 AWS',
 days:4, totalMin:1320, level:'世界赛',
 notes:[
  '官方技术描述 TD53 明确：四天赛程中两天整日排障、两天仅下午排障 —— 排错占赛场时间约四分之三',
  '前两日：独立完成 ①保险行业智能识别系统 ②股票基金交易云端自动化系统 的搭建、部署与运维',
  '决胜日：批量攻克工业互联网、生成式 AI、云安全运维等复杂故障，并完成高难度物联网实时数据处理',
  '公有云平台为 AWS（亚马逊云科技），赛项号 Skill 53',
  'WSOS 2026 上海版新增/强调四类角色：云架构师、DevOps 工程师、云原生开发者、云安全工程师'
 ],
 modules:[
  {id:'A', name:'第 1–2 日 · 两大系统交付', w:60, mins:660, groups:[
    {id:'SYS1', t:'保险行业智能识别系统', tasks:[
      {id:'sys1_01', d:'VPC 与子网规划（公私分离）', p:12, scn:'web1'},
      {id:'sys1_02', d:'业务服务部署与反向代理', p:14, scn:'ha1'},
      {id:'sys1_03', d:'健康检查与高可用', p:14, scn:'ha2'},
      {id:'sys1_04', d:'权限与安全基线', p:10, scn:'sys1'}
    ]},
    {id:'SYS2', t:'股票基金交易云端自动化系统', tasks:[
      {id:'sys2_01', d:'数据库与数据持久化', p:12, scn:'db1'},
      {id:'sys2_02', d:'容器化交付', p:14, scn:'docker1'},
      {id:'sys2_03', d:'自动化与幂等脚本', p:14, scn:'ans1'},
      {id:'sys2_04', d:'备份与恢复', p:10, scn:'bak1'}
    ]}
  ]},
  {id:'D', name:'决胜日 · 复杂故障批量排查（约占 3/4 时间）', w:40, mins:480, groups:[
    {id:'FIX', t:'故障排查主战场', tasks:[
      {id:'fix_01', d:'服务不可用（nginx 起不来）', p:20, scn:'fix1'},
      {id:'fix_02', d:'磁盘爆满', p:20, scn:'fix2'},
      {id:'fix_03', d:'403 权限异常', p:20, scn:'fix3'},
      {id:'fix_04', d:'DNS 解析异常', p:20, scn:'dns1'},
      {id:'fix_05', d:'虚拟机与用户体系混乱', p:20, scn:'sys1'}
    ]},
    {id:'IOT', t:'物联网实时数据处理', tasks:[
      {id:'iot_01', d:'实时采集与可视化', p:40, scn:'room3'},
      {id:'iot_02', d:'自动化巡检与告警', p:40, scn:'room2'}
    ]}
  ]}
 ],
 wsos:WSOS2026
};

COMPS['cn-prov']={
 id:'cn-prov', name:'国内省赛选拔 · 云计算赛项（公有云 A/B/C 三模块）',
 sub:'依据河南省第 46 届世赛选拔赛技术文件：3 模块 · 6 小时 · AWS GameDay 系统统一命题自动评分',
 days:1, totalMin:360, level:'省赛',
 notes:[
  '模块 A 公有云环境创建：依据设计图纸配置系统网络连接，在公有云平台创建/删除资源，规格型号须与要求一致',
  '模块 B 公有云业务部署：考察公有云服务使用能力，创建云存储等服务，通过各种方式维护和使用',
  '模块 C 公有云综合运维：在申请的公有云资源上部署应用，进行运维与故障排查，最终启动应用并提供正常服务',
  '总时长 6 小时；赛前 2 周公布样题，样题模块不作为最终竞赛的方式和内容',
  '选手须 2001-01-01 以后出生（云计算属世赛放宽年龄组）'
 ],
 modules:[
  {id:'A', name:'模块 A · 公有云环境创建', w:30, mins:120, groups:[
    {id:'A-ENV', t:'环境与网络', tasks:[
      {id:'cnA_01', d:'Web 服务环境搭建', p:15, scn:'web1'},
      {id:'cnA_02', d:'多站点虚拟主机', p:15, scn:'web2'}
    ]}
  ]},
  {id:'B', name:'模块 B · 公有云业务部署', w:40, mins:150, groups:[
    {id:'B-BIZ', t:'业务服务与数据', tasks:[
      {id:'cnB_01', d:'数据库建库授权', p:14, scn:'db1'},
      {id:'cnB_02', d:'建表与数据操作', p:13, scn:'db2'},
      {id:'cnB_03', d:'容器化部署业务', p:13, scn:'docker1'}
    ]}
  ]},
  {id:'C', name:'模块 C · 公有云综合运维（含故障排查）', w:30, mins:90, groups:[
    {id:'C-OPS', t:'运维与排障', tasks:[
      {id:'cnC_01', d:'负载均衡与健康检查', p:10, scn:'ha1'},
      {id:'cnC_02', d:'故障排查：服务不可用', p:10, scn:'fix1'},
      {id:'cnC_03', d:'故障排查：磁盘与权限', p:10, scn:'fix2'}
    ]}
  ]}
 ],
 wsos:WSOS2026
};

COMPS['brics']={
 id:'brics', name:'金砖国家职业技能大赛 · 云计算赛项',
 sub:'2 人/队实操 · 三模块：OpenStack 平台部署运维 / 容器云 / 企业级应用自动化部署与运维',
 days:2, totalMin:480, level:'国际赛',
 notes:[
  '主办：金砖国家工商理事会 + 俄罗斯科学和高等教育部；中方组织：教育部中外人文交流中心',
  '考核依据《云计算工程技术人员国家职业技术技能标准》，三模块均为实操',
  '更细考点：云主机配置、OpenStack 私有云运维、容器技术、Shell 脚本管资源、自动化运维工具、负载均衡',
  '⚠️ 2025 年中国赛区 25 个赛项中无「云计算」，是否回归待观察'
 ],
 modules:[
  {id:'M1', name:'模块一 · OpenStack 平台部署与运维', w:35, mins:180, groups:[
    {id:'M1-G', t:'私有云平台搭建', tasks:[
      {id:'brics1_01', d:'Web 服务与虚拟主机（平台侧验证）', p:18, scn:'web1'},
      {id:'brics1_02', d:'高可用与负载均衡', p:17, scn:'ha1'}
    ]}
  ]},
  {id:'M2', name:'模块二 · 容器云', w:35, mins:150, groups:[
    {id:'M2-C', t:'容器化应用部署', tasks:[
      {id:'brics2_01', d:'容器化部署网站', p:18, scn:'docker1'},
      {id:'brics2_02', d:'可伸缩与健康检查', p:17, scn:'ha2'}
    ]}
  ]},
  {id:'M3', name:'模块三 · 企业级应用自动化部署与运维', w:30, mins:150, groups:[
    {id:'M3-A', t:'自动化与性能监测', tasks:[
      {id:'brics3_01', d:'Ansible 剧本与幂等', p:15, scn:'ans1'},
      {id:'brics3_02', d:'备份与定时任务', p:15, scn:'bak1'}
    ]}
  ]}
 ],
 wsos:WSOS2026
};

COMPS['cn-private']={
 id:'cn-private', name:'国赛 / 职业院校技能大赛 · 云计算应用（私有云路线）',
 sub:'与世赛公有云路线是两回事 · 2026 欧拉 + OpenStack Yoga',
 days:1, totalMin:360, level:'国赛',
 notes:[
  '⚠️ 与世赛公有云路线技术栈不同，不要混着学',
  '2026 国赛路线：基于 openEuler 22.09 搭建 Yoga 版本 OpenStack',
  '赛制已改版：由三套系统整合为「综合竞赛平台」',
  '私有云 + 容器云 + 自动化运维三块为主'
 ],
 modules:[
  {id:'P1', name:'私有云平台（OpenStack）', w:40, mins:180, groups:[
    {id:'P1-O', t:'平台部署与运维', tasks:[
      {id:'priv1_01', d:'计算与网络服务', p:20, scn:'web1'},
      {id:'priv1_02', d:'镜像与实例交付', p:20, scn:'room1'}
    ]}
  ]},
  {id:'P2', name:'容器云', w:35, mins:120, groups:[
    {id:'P2-C', t:'容器平台', tasks:[
      {id:'priv2_01', d:'容器化部署与编排', p:18, scn:'docker1'},
      {id:'priv2_02', d:'高可用与伸缩', p:17, scn:'ha2'}
    ]}
  ]},
  {id:'P3', name:'自动化运维', w:25, mins:60, groups:[
    {id:'P3-A', t:'自动化与基线', tasks:[
      {id:'priv3_01', d:'Ansible 幂等交付', p:13, scn:'ans1'},
      {id:'priv3_02', d:'基线与巡检脚本', p:12, scn:'room3'}
    ]}
  ]}
 ],
 wsos:WSOS2026
};

E.COMPETITIONS=COMPS;
E.competitionById=function(id){ return COMPS[id]||null; };
E.competitionList=function(){
  return Object.keys(COMPS).map(function(k){
    var c=COMPS[k];
    return {id:c.id,name:c.name,sub:c.sub,level:c.level,days:c.days,totalMin:c.totalMin,
            modules:c.modules.length,taskCount:E.compTaskCount(c)};
  });
};
E.compTaskCount=function(c){
  var n=0;
  c.modules.forEach(function(m){
    if(m.groups) m.groups.forEach(function(g){ n+=(g.tasks||[]).length; });
  });
  if(c.modules.some(function(m){return m.hosts;})) n+=c.modules.filter(function(m){return m.hosts;})[0].hosts.length;
  return n;
};

/* ================= 进度记录 ================= */
/** 仿真场 VM 上挂一份 per-task 记录：f() 任务实时判，scn 任务按完成记录计 */
E.compProg=function(vm,compId){
  if(!vm.compProg) vm.compProg={};
  if(!vm.compProg[compId]) vm.compProg[compId]={};
  return vm.compProg[compId];
};
/** 场景类任务完成后调用：pct 为该场景得分率（0-100） */
E.compRecord=function(vm,compId,taskId,pct){
  var r=E.compProg(vm,compId);
  r[taskId]=Math.max(0,Math.min(100,pct|0));
  return r;
};
E.compClear=function(vm,compId){ if(vm.compProg) delete vm.compProg[compId]; };

/* ================= 判分 ================= */
/**
 * 逐题判分。
 *  · 带 f() 的任务：直接在赛项 VM 上实时判定（真·可自动验证）
 *  · 引用实训场景的任务：按「完成记录」得分率折算，默认 0
 *    （不可在共享 VM 上直接判——各场景 setup 互相冲突，会串味）
 */
E.compGrade=function(vm,compId){
  var c=COMPS[compId];
  if(!c) return null;
  var prog=E.compProg(vm,compId);
  var mods=[], liveCount=0, taskSum=0, taskGot=0;
  c.modules.forEach(function(m){
    var groups=[];
    if(m.groups) m.groups.forEach(function(g){
      var ts=(g.tasks||[]).map(function(t){
        var got=false, msg='', kind='f';
        if(t.f){
          var r=null;
          try{ r=t.f(vm); }catch(e){ r={ok:false,msg:'判定异常'}; }
          got=!!r.ok; msg=r.msg||''; kind='f'; liveCount++;
        } else if(t.scn){
          kind='scn';
          var pct=prog[t.id];
          got=(typeof pct==='number'&&pct>=100);
          msg=typeof pct==='number' ? ('实训得分率 '+pct+'%'+(pct<100?'（未满分不计入）':'')) : '未完成';
        }
        taskSum+=t.p; if(got) taskGot+=t.p;
        return {id:t.id,d:t.d,p:t.p,ok:got,msg:msg,kind:kind,scn:t.scn||null};
      });
      var sum=ts.reduce(function(a,b){return a+b.p;},0);
      var gp=ts.reduce(function(a,b){return a+(b.ok?b.p:0);},0);
      groups.push({id:g.id,t:g.t,tasks:ts,sum:sum,got:gp,pct:sum?Math.round(gp/sum*100):0});
    });
    if(m.hosts) m.hosts.forEach(function(h){
      groups.push({id:h.id,t:h.t,checklist:h.items,host:true,sum:h.items.length,got:0,pct:0});
    });
    var sum2=groups.reduce(function(a,g){return a+g.sum;},0);
    var got2=groups.reduce(function(a,g){return a+g.got;},0);
    mods.push({id:m.id,name:m.name,w:m.w,mins:m.mins,groups:groups,sum:sum2,got:got2,
               pct:sum2?Math.round(got2/sum2*100):0});
  });
  var full=mods.reduce(function(a,m){return a+m.sum;},0);
  var total=mods.reduce(function(a,m){return a+m.got;},0);
  var taskMods=mods.filter(function(m){return !m.groups.some(function(g){return g.host;});});
  var weighted=taskMods.reduce(function(a,m){return a+m.pct*m.w/100;},0);
  /* 逐日时间预算 */
  var days=[];
  for(var d=0;d<(c.days||1);d++){
    var dm=mods.filter(function(m){return d===0||m.id!=='A';});
    days.push({day:d+1,mins:Math.round(c.totalMin/(c.days||1))});
  }
  return {compId:compId, comp:c, modules:mods,
          total:total, full:full, pct:full?Math.round(total/full*100):0,
          weighted:Math.round(weighted*10)/10,
          liveCount:liveCount, taskSum:taskSum, taskGot:taskGot,
          days:days, checkedAt:new Date().toISOString()};
};

/** WSOS 八项权重与本场得分的对照（自评用） */
E.compWsosMap=function(compId,report){
  var c=COMPS[compId];
  if(!c) return null;
  return (c.wsos||[]).map(function(w,i){
    return {i:i+1,k:w.k,weight:w.w,note:w.note,
            est:Math.round(w.w*(report?Math.min(100,report.weighted):0)/100)};
  });
};

/* ================= 环境准备 ================= */
/** 按赛事预置初始环境：目录骨架、占位配置、部分已给分（模拟“部分环境已就绪”） */
E.compSetup=function(vm,compId,opts){
  opts=opts||{};
  var c=COMPS[compId];
  if(!c) return false;
  var D=vm.mkdirP?function(p){vm.mkdirP(p);}:function(){};
  ['/etc/iptables','/etc/ssl/ca','/etc/ssl/certs','/etc/wireguard','/etc/squid','/etc/postfix',
   '/etc/bind','/etc/samba','/etc/ansible','/var/www/html','/srv/public','/srv/share/homework',
   '/root'].forEach(D);
  /* 试题册：把当前赛事的任务书写进文件，考生可 cat */
  var lines=[];
  lines.push('# '+c.name);
  lines.push('# '+c.sub);
  lines.push('');
  c.modules.forEach(function(m){
    lines.push('## '+m.name+'  [权重 '+m.w+'%]  建议用时 '+m.mins+' 分钟');
    (m.groups||[]).forEach(function(g){
      lines.push('');
      lines.push('### '+g.id+' '+g.t);
      (g.tasks||[]).forEach(function(t){ lines.push('  ['+t.p+'分] '+t.id+'  '+t.d); });
      (g.checklist||[]).forEach(function(it){ lines.push('  [ ] '+it); });
    });
    if(m.hosts) m.hosts.forEach(function(h){
      lines.push('');
      lines.push('### '+h.id+' '+h.t);
      h.items.forEach(function(it){ lines.push('  [ ] '+it); });
    });
  });
  lines.push('');
  lines.push('# 官方赛题赛前保密，此处为按官方评分脚本还原的模拟题书。');
  vm.write('/root/TASKBOOK.md', lines.join('\n'));
  if(opts.base!==false){
    /* 部分基础件：DNS 与 HAProxy 给一个能跑的起点，模拟「部分环境已就绪」 */
    if(!R(vm,'/etc/dnsmasq.conf')) vm.write('/etc/dnsmasq.conf','# 待配置\n');
    if(!R(vm,'/etc/haproxy/haproxy.cfg')) vm.write('/etc/haproxy/haproxy.cfg','# 待配置\n');
    if(!R(vm,'/etc/ssh/sshd_config')) vm.write('/etc/ssh/sshd_config','Port 22\nPermitRootLogin no\n');
    if(!R(vm,'/etc/nginx/nginx.conf')){
      var ng=vm.svcs['nginx'];
      if(ng&&ng.snap!==undefined){ /* 保留引擎默认 */ }
    }
  }
  return true;
};

})(typeof window!=='undefined'?window:(typeof globalThis!=='undefined'?globalThis:this));
