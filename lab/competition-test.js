/* =====================================================================
   competition-test.js · 竞赛仿真场测试
   ------------------------------------------------------------
   核心断言：里昂 2024 Module A 的 52 个官方评分点**每一个都可达**。
   做法是模拟一个满分选手把活全干完，再断言 52/52 全绿。
   若某个判据依赖仿真器不支持的能力，这里会失败（等于提前发现死分）。
   跑法： cd lab && node competition-test.js
   ===================================================================== */
'use strict';
var E=require('./lab-engine.js');
require('./lab-extras.js');
require('./lab-scenarios.js');
require('./competition.js');

var fail=0;
function ok(c,m){ console.log((c?'  ✅ ':'  ❌ ')+m); if(!c) fail++; }

console.log('=== 1. 赛事清单 ===');
var list=E.competitionList();
ok(list.length===5, '赛事数 = '+list.length+'（期望 5）');
list.forEach(function(c){ console.log('     ['+c.level+'] '+c.name+' · '+c.modules+' 模块 · '+c.taskCount+' 项'); });

console.log('=== 2. 里昂 2024 结构 ===');
var lyon=E.competitionById('ws-lyon24');
ok(!!lyon, '赛事已注册');
var mA=lyon.modules.filter(function(m){return m.id==='A';})[0];
ok(!!mA, 'Module A 存在');
var tasks=[];
mA.groups.forEach(function(g){ tasks=tasks.concat(g.tasks||[]); });
ok(mA.groups.length===16, '评分点组数 = '+mA.groups.length+'（期望 A01–A16）');
ok(tasks.length===52, '官方任务编号数 = '+tasks.length+'（期望 52）');
ok(tasks[0].id==='task_A01_01' && tasks[tasks.length-1].id==='task_A16_05',
   '编号原样：'+tasks[0].id+' … '+tasks[tasks.length-1].id);
var sum=0; mA.groups.forEach(function(g){ g.tasks.forEach(function(t){ sum+=t.p; }); });
ok(sum===245, 'Module A 满分合计 = '+sum+'（期望 245）');
var lyonB=lyon.modules.filter(function(m){return m.id==='B';})[0];
ok(!!lyonB && lyonB.hosts.length===8, 'Module B 主机数 = '+(lyonB?lyonB.hosts.length:0)+'（期望 8）');
ok(E.COMPETITIONS['ws-lyon24'].wsos.length===8, 'WSOS 权重项 = 8');
ok(lyon.wsos.reduce(function(a,w){return a+w.w;},0)===100, 'WSOS 权重合计 = 100');

console.log('=== 3. 初始状态必须 0 分（无白送分） ===');
var vm=E.newVM('ct');
E.compSetup(vm,'ws-lyon24');
var r0=E.compGrade(vm,'ws-lyon24');
ok(r0.total===0, '初始得分 = '+r0.total+' / '+r0.full);
var green0=0;
r0.modules.forEach(function(m){ m.groups.forEach(function(g){ (g.tasks||[]).forEach(function(t){ if(t.ok) green0++; }); }); });
ok(green0===0, '初始达标项 = '+green0+'（期望 0）');
ok(vm.read('/root/TASKBOOK.md')!==null, '题书已生成 /root/TASKBOOK.md');
ok((vm.read('/root/TASKBOOK.md')||'').indexOf('task_A01_01')>=0, '题书含官方评分点编号');

console.log('=== 4. 满分求解：52 个评分点必须全部可达 ===');
var x=function(c){ E.execLine(vm,c); };
var W=function(p,c){ vm.mkdirP(p.replace(/\/[^\/]*$/,'')); vm.write(p,c); };
['ldap','haproxy','squid','postfix','samba','slapd','dnsmasq','nginx','iproute2','wireguard','cron'].forEach(function(p){ x('apt install -y '+p); });
['slapd','haproxy','squid','postfix','smbd','dnsmasq','nginx'].forEach(function(s){ x('systemctl start '+s); });
x('groupadd -f Employees');
x('useradd -m -s /bin/bash jamie'); x('useradd -m -s /bin/bash peter'); x('useradd -m admin');
W('/root/base.ldif','dn: ou=Employees,dc=paris,dc=local\nobjectClass: organizationalUnit\nou: Employees\n\ndn: uid=jamie,ou=Employees,dc=paris,dc=local\nobjectClass: inetOrgPerson\nuid: jamie\ncn: Jamie\nsn: Lee\n');
x('ldapadd -x -f /root/base.ldif');
W('/etc/ssl/ca/root.crt','-----BEGIN CERTIFICATE-----\nsubject=CN=Example Root CA\nissuer=CN=Example Root CA\nX509v3 Basic Constraints: critical CA:TRUE\n-----END CERTIFICATE-----\n');
W('/etc/ssl/ca/services.crt','-----BEGIN CERTIFICATE-----\nsubject=CN=Services CA\n-----END CERTIFICATE-----\n');
W('/etc/ssl/certs/web.crt','-----BEGIN CERTIFICATE-----\nsubject=CN=web.paris.local\n-----END CERTIFICATE-----\n');
W('/etc/ssl/certs/mail.crt','-----BEGIN CERTIFICATE-----\nsubject=CN=mail.paris.local\n-----END CERTIFICATE-----\n');
W('/etc/samba/smb.conf','[global]\n  workgroup = WORKGROUP\n[public]\n  path = /srv/public\n  read only = no\n  guest ok = no\n[internal]\n  path = /srv/share/homework\n  read only = no\n  guest ok = no\n');
W('/etc/bind/db.paris.local','$TTL 604800\n@ IN SOA ns1.paris.local. admin.paris.local. ( 2026 3600 600 604800 60 )\nint-srv01 IN A 192.168.10.20\n_ldap._tcp.int-srv01 IN SRV 10 0 389 int-srv01\nmail IN A 192.168.10.25\nmail IN AAAA 2001:db8::25\nweb IN CNAME int-srv01\nprx-vrrp IN A 192.168.10.30\n');
W('/etc/bind/named.conf.options','options { recursion yes; };\n');
W('/etc/bind/named.conf.local','zone "paris.local" { type slave; file "db.paris.local"; masters { 192.168.10.53; }; };\nzone "10.168.192.in-addr.arpa" { type slave; file "db.10.168.192.in-addr.arpa"; masters { 192.168.10.53; }; };\n');
W('/etc/bind/db.10.168.192.in-addr.arpa','$TTL 604800\n@ IN SOA ns1.paris.local. admin.paris.local. ( 2026 3600 600 604800 60 )\n20.10 IN PTR int-srv01.paris.local.\n');
W('/etc/bind/db.10.168.192.ip6.arpa','$TTL 604800\n@ IN SOA ns1.paris.local. admin.paris.local. ( 2026 3600 600 604800 60 )\n25 IN PTR mail.paris.local.\n');
x('systemctl restart dnsmasq');
x('sysctl -w net.ipv4.ip_forward=1'); x('sysctl -w net.ipv6.conf.all.forwarding=1');
x('iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE');
W('/etc/wireguard/wg0.conf','[Interface]\nAddress = 10.10.0.1/24\nListenPort = 51820\nPrivateKey = gJ8=\n[Peer]\nPublicKey = xTIBA5=\nPresharedKey = YCLpHSZbX0bkvbatdWZmaw==\nAllowedIPs = 10.10.0.2/32\n');
x('wg-quick up wg0');
W('/etc/squid/squid.conf','http_port 3128 intercept\nacl localnet SRC 192.168.10.0/24\nhttp_access allow localnet\n');
W('/etc/postfix/main.cf','myhostname = mail.paris.local\nmydomain = paris.local\nmyorigin = $mydomain\ninet_interfaces = all\n');
x('sendmail -f jamie@paris.local -t admin@paris.local');
W('/etc/fstab','UUID=1234-5678 /srv/data ext4 defaults 0 2\n');
W('/root/backup.sh','#!/bin/bash\ntar czf /backup/b.tgz /etc\n');
W('/var/spool/cron/crontabs/root','0 3 * * * /root/backup.sh\n');
W('/etc/ssh/sshd_config','Port 22\nPubkeyAuth yes\nTrustedUserCAKeys /etc/ssl/ca/root.crt\n');
W('/etc/haproxy/haproxy.cfg','global\n  log stdout\ndefaults\n  mode http\nfrontend http_in\n  bind *:80\n  bind *:443 ssl crt /etc/ssl/certs/web.crt\n  redirect scheme https\n  http-request set-header X-Proto https\nbackend webservers\n  server web1 192.168.10.11:80 check\nfrontend dns_fwd\n  bind *:53 udp\nfrontend mail_fwd\n  bind *:143\n  tcp-request content accept\nbackend mail\n  server mail1 192.168.10.25:143 starttls\n');
W('/etc/keepalived/keepalived.conf','vrrp_instance VI_1 {\n  virtual_ipaddress {\n    192.168.10.40\n  }\n}\n');
W('/var/www/html/main.html','<h1>TheErasTour 2024</h1>\n');
W('/var/www/html/404.html','<h1>Not Found</h1>\n');
W('/etc/ansible/hosts','[webservers]\nweb1 ansible_host=192.168.10.11\n');
W('/root/play.yml','- hosts: webservers\n  tasks:\n    - copy:\n        src: /var/www/html/main.html\n        dest: /var/www/html/main.html\n');
x('systemctl restart haproxy');

var r1=E.compGrade(vm,'ws-lyon24');
var mA1=r1.modules.filter(function(m){return m.id==='A';})[0];
var dead=[];
mA1.groups.forEach(function(g){ g.tasks.forEach(function(t){ if(!t.ok) dead.push(t); }); });
ok(dead.length===0, 'Module A 满分求解 = '+mA1.got+'/'+mA1.sum+'（'+mA1.pct+'%），不可达评分点 '+dead.length);
dead.forEach(function(t){ console.log('       ❌ '+t.id+' ['+t.p+'] '+t.d+' — '+(t.msg||'')); });
ok(mA1.got===245, 'Module A 得分 = '+mA1.got+'（期望 245/245）');

console.log('=== 5. 其余赛事可判分 ===');
['ws-shanghai26','cn-prov','brics','cn-private'].forEach(function(id){
  var v2=E.newVM('t2'); E.compSetup(v2,id);
  var rr=E.compGrade(v2,id);
  ok(!!rr && rr.full>0, id+' 判分可用，满分 '+rr.full);
});

console.log('');
console.log('='.repeat(58));
console.log(fail===0 ? '竞赛仿真场测试：全部通过 ✅' : ('竞赛仿真场测试：'+fail+' 项失败 ❌'));
process.exit(fail?1:0);
