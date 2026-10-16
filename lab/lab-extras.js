/* =====================================================================
   lab-extras.js · 竞赛模块补齐件
   ------------------------------------------------------------
   为「世赛云计算仿真」补上 Module A 里现有引擎缺失的部件：
   · sysctl   —— 内核转发开关（A05 评分点）
   · iptables —— 真实规则模型 + SNAT/MASQUERADE/DNAT/端口转发（A06 / A16）
   · wg      —— WireGuard 接口与 PSK（A07）
   · squid   —— 透明代理（A08）
   · postfix —— 邮件服务与 sendmail（A09）
   · x509    —— 证书链检查（A02）
   纯 JS 无依赖，浏览器/Node 双兼容。挂在 LabEngine.EXTRAS 上，
   由 competition.js 装载后并入 CMDS。
   ===================================================================== */
(function(root){
'use strict';
var E=root.LabEngine;
if(!E) return;
var C=E.C, notFound=function(n){ return {lines:[{s:'bash: '+n+': command not found',c:'err'}], code:127}; };

/* ---------- 通用小工具 ---------- */
function ok(s){ return {lines:[C(s)], code:0}; }
function bad(s){ return {lines:[C(s,'err')], code:1}; }
function yn(b){ return b?'yes':'no'; }
function readOr(vm,p,def){
  var s=vm.read(p); return (s===null||s===undefined)?def:String(s);
}
/** 解析 /etc/sysctl.d/99-cloud.conf 之类的 key = value 文件 */
function parseKV(vm,path){
  var s=readOr(vm,path,''), o={};
  s.split('\n').forEach(function(l){
    l=l.replace(/#.*$/,'').trim();
    if(!l) return;
    var i=l.indexOf('=');
    if(i<0) return;
    o[l.slice(0,i).trim()]=l.slice(i+1).trim();
  });
  return o;
}

/* ================== sysctl ================== */
var SYSCTL_DEFAULT={
  'net.ipv4.ip_forward':'0',
  'net.ipv6.conf.all.forwarding':'0',
  'net.ipv4.conf.default.rp_filter':'2',
  'net.ipv4.conf.all.rp_filter':'2'
};
E.extras_sysctlParse=function(vm){
  var kv=parseKV(vm,'/etc/sysctl.conf');
  var kv2=parseKV(vm,'/etc/sysctl.d/99-cloud.conf');
  var o={};
  var k;
  for(k in SYSCTL_DEFAULT) o[k]=SYSCTL_DEFAULT[k];
  for(k in kv) o[k]=kv[k];
  for(k in kv2) o[k]=kv2[k];
  return o;
};
function sysctlState(vm){
  if(!vm.sysctl) vm.sysctl=E.extras_sysctlParse(vm);
  return vm.sysctl;
}

/* ================== iptables（含 NAT） ================== */
var IPT_DEF='*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:POSTROUTING ACCEPT [0:0]\nCOMMIT\n';
function parseIptables(vm){
  var s=readOr(vm,'/etc/iptables/rules.v4',IPT_DEF), o={filter:{},nat:{}};
  var cur=null;
  s.split('\n').forEach(function(line){
    var m;
    if((m=line.match(/^\*(\w+)/))){ cur=m[1]; o[cur]=o[cur]||{}; return; }
    if(line==='COMMIT'){ cur=null; return; }
    if(line.charAt(0)===':'||!line.trim()) return;
    if(cur) o[cur][line.trim()]=true;
  });
  return o;
}
E.extras_iptablesParse=function(vm){
  var st=parseIptables(vm);
  // 由 -L 风格输出反推规则顺序：保持插入序
  if(!vm.ipt) vm.ipt={filter:[],nat:[]};
  if(!vm.ipt._loaded){ vm.ipt._loaded=true; }
  return st;
};
function iptState(vm){
  if(!vm.ipt) vm.ipt={filter:[],nat:[],_loaded:false};
  if(!vm.ipt._loaded){
    vm.ipt._loaded=true;
    var st=parseIptables(vm);
    vm.ipt.filter=Object.keys(st.filter||{});
    vm.ipt.nat=Object.keys(st.nat||{});
  }
  return vm.ipt;
}
function iptFlushToFile(vm){
  var t=vm.ipt;
  if(vm.mkdirP) vm.mkdirP('/etc/iptables');
  var out='*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n';
  t.filter.forEach(function(r){ out+=r+'\n'; });
  out+='COMMIT\n*nat\n:PREROUTING ACCEPT [0:0]\n:POSTROUTING ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n';
  t.nat.forEach(function(r){ out+=r+'\n'; });
  out+='COMMIT\n';
  vm.write('/etc/iptables/rules.v4', out);
}
/** 判断某条链上是否满足一条能力，返回 {ok,msg} */
E.extras_iptablesHas=function(vm,table,chain,matcher){
  var t=iptState(vm);
  var arr=t[table]||[];
  for(var i=0;i<arr.length;i++){
    if(arr[i].indexOf('-'+chain+' ')<0 && arr[i].indexOf('-A '+chain+' ')<0) continue;
    if(matcher(arr[i])) return {ok:true,rule:arr[i]};
  }
  return {ok:false};
};

/* ================== WireGuard ================== */
E.extras_wgState=function(vm){
  var s=readOr(vm,'/etc/wireguard/wg0.conf','');
  var o={exists:false,iface:null,priv:null,addr:null,listen:null,peers:[]};
  if(!s.trim()) return o;
  o.exists=true; o.iface='wg0';
  s.split('\n').forEach(function(l){
    l=l.replace(/#.*$/,'').trim();
    if(!l) return;
    var m;
    if((m=l.match(/^(PrivateKey|PrivateKey\s*=)\s*(\S+)/))){ o.priv=m[3]; }
    else if(/^Address/.test(l)){ o.addr=l.replace(/^Address\s*=?\s*/,'').trim(); }
    else if(/^ListenPort/.test(l)){ o.listen=l.replace(/^ListenPort\s*=?\s*/,'').trim(); }
    else if((m=l.match(/^\[Peer\]/))){ o.peers.push({}); }
    else if(o.peers.length){
      if(/^PublicKey/.test(l)) o.peers[o.peers.length-1].pub=l.replace(/^PublicKey\s*=?\s*/,'').trim();
      if(/^PresharedKey/.test(l)) o.peers[o.peers.length-1].psk=l.replace(/^PresharedKey\s*=?\s*/,'').trim();
      if(/^AllowedIPs/.test(l)) o.peers[o.peers.length-1].allowed=l.replace(/^AllowedIPs\s*=?\s*/,'').trim();
      if(/^Endpoint/.test(l)) o.peers[o.peers.length-1].ep=l.replace(/^Endpoint\s*=?\s*/,'').trim();
    }
  });
  return o;
};

/* ================== Squid ================== */
E.extras_squidParse=function(vm){
  var s=readOr(vm,'/etc/squid/squid.conf',''), o={ports:8080,mode:'http_port',acl:{},dst:[]};
  s.split('\n').forEach(function(l){
    l=l.replace(/#.*$/,'').trim();
    if(!l) return;
    var m;
    if((m=l.match(/^http_port\s+(\d+)/))){ o.ports=+m[1]; o.mode='http_port'; }
    if((m=l.match(/^(\w+)_port\s+(\d+)/))){ o.ports=+m[2]; o.mode=m[1]+'_port'; }
    if((m=l.match(/^(http|https|ftp|localnet)\s+(SRC|DST)\s+(\S+)/))) o.acl[m[1]]=m[3];
    if(/^http_port/.test(l)&&/intercept/.test(l)) o.intercept=true;
  });
  return o;
};

/* ================== Postfix ================== */
E.extras_postfixParse=function(vm){
  var s=readOr(vm,'/etc/postfix/main.cf',''), o={};
  s.split('\n').forEach(function(l){
    l=l.replace(/#.*$/,'').trim();
    if(!l) return;
    var m;
    if((m=l.match(/^([\w_]+)\s*=\s*(.+)$/))) o[m[1].toLowerCase()]=m[2].trim();
  });
  return o;
};
function mailQ(vm){
  if(!vm.mailq) vm.mailq=[];
  return vm.mailq;
}

/* ================== 命令实现 ================== */
var X={};

/* --- sysctl --- */
X['sysctl']=function(vm,args){
  var st=sysctlState(vm);
  if(args[0]==='-a'||args[0]==='-A'||args.length===0){
    var out=[];
    for(var k in st) out.push(k+' = '+st[k]);
    return ok(out.join('\n'));
  }
  if(args[0]==='-w'||args[0]==='-p'){
    // sysctl -w key=value
    var a=args.slice(1), i=0;
    if(a[0]==='-p') i=1;
    for(;i<a.length;i++){
      var m=a[i].match(/^([\w.]+)\s*=\s*(\S+)$/);
      if(!m) return bad('sysctl: 非法参数: '+a[i]);
      vm.sysctl=st; st[m[1]]=m[2];
    }
    // 落盘到 /etc/sysctl.d/99-cloud.conf
    var txt='# 由 sysctl -w 写入\n';
    for(var kk in st) txt+=kk+' = '+st[kk]+'\n';
    vm.write('/etc/sysctl.d/99-cloud.conf',txt);
    var r=[];
    for(var k2 in st) r.push(k2+' = '+st[k2]);
    return ok(r.join('\n'));
  }
  var key=args[0];
  if(key.indexOf('=')>0){
    var m2=key.match(/^([\w.]+)=(\S+)$/);
    if(m2){ st=st; vm.sysctl=st; st[m2[1]]=m2[2]; return ok(m2[1]+' = '+m2[2]); }
  }
  if(st[key]===undefined) return bad('sysctl: cannot stat /proc/sys/'+key.replace(/\./g,'/')+': No such file or directory');
  return ok(key+' = '+st[key]);
};

/* --- iptables --- */
X['iptables']=function(vm,args){
  if(!vm.ipt) vm.ipt={filter:[],nat:[],_loaded:false};
  var t=iptState(vm), a=args, table='filter';
  var i=0;
  if(a[0]==='-t'){ table = a[1]==='nat'?'nat':'filter'; i=2; }
  var verb=a[i], chain=null, rule=[];
  if(verb && verb.charAt(0)==='-'){
    verb=verb.replace(/^-+/,'');
  } else if(verb){
    return ok('（iptables v1.8.7 (nf_tables) 模拟器：支持 -A -I -D -F -L -S -t nat）');
  }
  i++;
  // 解析链
  if(a[i] && a[i].charAt(0)!=='-'){ chain=a[i]; i++; }
  for(;i<a.length;i++) rule.push(a[i]);
  var line=(chain? '-A '+chain+' ':'-A ')+rule.join(' ');

  if(verb==='L'||verb==='nL'||verb==='ln'||verb==='nl'){
    var out=['Chain '+chain+' (policy ACCEPT)','target     prot opt source               destination'];
    (vm.ipt[table]||[]).forEach(function(r){
      if(!chain || r.indexOf('-A '+chain+' ')<0) return;
      out.push('ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            '+r.replace('-A '+chain+' ',''));
    });
    return ok(out.join('\n'));
  }
  if(verb==='S'){
    var o2=['*'+table+':',':PREROUTING ACCEPT [0:0]',':INPUT ACCEPT [0:0]',':POSTROUTING ACCEPT [0:0]',':OUTPUT ACCEPT [0:0]'];
    (vm.ipt[table]||[]).forEach(function(r){ if(!chain||r.indexOf('-A '+chain+' ')===0) o2.push(r); });
    o2.push('COMMIT');
    return ok(o2.join('\n'));
  }
  if(verb==='F'){
    if(chain) vm.ipt[table]=(vm.ipt[table]||[]).filter(function(r){ return r.indexOf('-A '+chain+' ')!==0; });
    else vm.ipt[table]=[];
    iptFlushToFile(vm); return ok('');
  }
  if(verb==='A'){ (vm.ipt[table]=vm.ipt[table]||[]).push(line); iptFlushToFile(vm); return ok(''); }
  if(verb==='I'){
    var arr=vm.ipt[table]=vm.ipt[table]||[];
    var pos=parseInt(rule.shift(),10); if(isNaN(pos)||pos<1) pos=1;
    arr.splice(pos-1,0,line); iptFlushToFile(vm); return ok('');
  }
  if(verb==='D'){
    var arr2=vm.ipt[table]=vm.ipt[table]||[];
    if(!chain) return bad('iptables: 需要链名');
    var idx=-1;
    for(var k=arr2.length-1;k>=0;k--) if(arr2[k]===line) idx=k;
    if(idx<0) return bad('iptables: Bad rule (does a matching rule exist in that chain?).');
    arr2.splice(idx,1); iptFlushToFile(vm); return ok('');
  }
  if(verb==='Z'){ vm.ipt[table]=[]; iptFlushToFile(vm); return ok(''); }
  if(verb==='C'||verb==='vC'){
    // 测试某条规则是否存在（评分用）
    var ch=a[i+1];
    return ok(yn(E.extras_iptablesHas(vm,table,ch,function(r){ return r===line||r.indexOf(line)>=0; }).ok));
  }
  return bad('iptables: 模拟器暂不支持该参数组合：'+args.join(' '));
};

/* --- nft（部分实现，指回 iptables） --- */
X['nft']=function(vm,args){
  return ok('（nft 模拟器：请使用 iptables -t nat，机房与比赛的常规武器）');
};

/* --- wg / wg-quick --- */
X['wg']=function(vm,args){
  var st=E.extras_wgState(vm);
  if(args[0]==='show'){
    var iface=args[1]||'wg0';
    if(!st.exists) return bad('Unable to access interface: No such device');
    var out=['interface: '+iface, '  public key: '+ (vm.wgPub||'(未生成)')];
    if(st.priv) out.push('  private key: (hidden)');
    if(st.listen) out.push('  listening port: '+st.listen);
    st.peers.forEach(function(p,i){
      out.push('peer: '+(p.pub||'?')+(p.psk?' (has PSK)':''));
      if(p.allowed) out.push('  allowed ips: '+p.allowed);
      if(p.ep) out.push('  endpoint: '+p.ep);
    });
    return ok(out.join('\n'));
  }
  if(args[0]==='--version') return ok('wireguard-tools v1.0.20210914');
  if(args[0]==='genkey'){ vm.write('/etc/wireguard/private.key','(generated)\n'); return ok(''); }
  if(args[0]==='genpsk'){ return ok('(generated PSK)'); }
  return bad('wg: 模拟器支持: show / genkey / genpsk / --version');
};
X['wg-quick']=function(vm,args){
  var a=args[0];
  if(a==='up'||a==='down'){
    var iface=args[1]||'wg0';
    var s=vm.svc('wg-quick-'+iface,true);
    if(a==='up'){ s.installed=true; s.running=true; s.enabled=true; }
    else { s.running=false; }
    return ok(a==='up' ? ("wg-quick: '# "+iface+" is up") : ("wg-quick: '# "+iface+" is down"));
  }
  return bad('wg-quick: 模拟器仅支持 up/down');
};

/* --- squid --- */
X['squid']=function(vm,args){
  if(!vm.pkgs['squid']) return notFound('squid');
  var p=E.extras_squidParse(vm);
  if(args[0]==='-k'&&args[1]==='parse'){
    var s=readOr(vm,'/etc/squid/squid.conf','');
    if(!s.trim()) return bad('squid: 配置文件为空');
    var badLine=null;
    s.split('\n').forEach(function(l,i){
      var t=l.replace(/#.*$/,'').trim(); if(!t) return;
      if(/^\w+_port\s+\d+/.test(t)) return;
      if(/^(acl|http_access|httpd_accel|cache_dir|cache_mem)\b/.test(t)) return;
      if(/^[a-z_]+\s+(SRC|DST)\b/.test(t)) return;
      if(/^\s/.test(l)&&/^\S/.test(t)) { if(!badLine) badLine=t; }
    });
    if(badLine) return bad('squid: FATAL: Bad configuration line: '+badLine);
    return ok('squid: configuration OK.');
  }
  if(args[0]==='-v'||args[0]==='--version') return ok('Squid Cache: Version 5.7\nService Name: squid\n');
  if(args[0]==='-k'&&args[1]==='shutdown'){ var s2=vm.svc('squid'); if(s2) s2.running=false; return ok(''); }
  return ok('（squid 模拟器：用 squid -k parse 检查配置，systemctl 管理服务）');
};

/* --- postfix / sendmail / mailq --- */
X['postfix']=function(vm,args){
  if(!vm.pkgs['postfix']) return notFound('postfix');
  if(args[0]==='check'){
    var c=E.extras_postfixParse(vm);
    if(!c['myhostname']) return bad('postfix: fatal: parameter myhostname: no valid value');
    if(!c['inet_interfaces']&&!c['inet_protocols']) return bad('postfix: warning: inet_interfaces 未设置，监听 localhost');
    return ok('postfix: the Postfix mail system is not running: '+ (vm.svcs['postfix']&&vm.svcs['postfix'].running?'(is running)':'check with "postfix status"'));
  }
  if(args[0]==='status'){ return ok('postfix/postfix-script: the Postfix mail system is '+(vm.svcs['postfix']&&vm.svcs['postfix'].running?'running':'not running')); }
  if(args[0]==='reload'){ return ok('postfix/postfix-script: refreshing the mail queue'); }
  return ok('（postfix 模拟器：postfix check / status / reload）');
};
X['sendmail']=function(vm,args){
  if(!vm.pkgs['postfix']) return notFound('sendmail');
  var from=null, to=[], body=[];
  for(var i=0;i<args.length;i++){
    var a=args[i];
    if(a==='-f'||a==='-r'){ from=args[++i]; continue; }
    if(a==='-t'||a==='-i'||a==='-v'||a==='-oi'||a==='-oem'||a.charAt(0)==='-') continue;
    to.push(a);
  }
  var subj='';
  for(var j=0;j<args.length;j++) if(args[j]==='-s'){ subj=args[j+1]||''; break; }
  var q=mailQ(vm);
  q.push({from:from||'root@localhost', to:to.join(', ')||'(收件人未指定)', subj:subj,
          ts:Date.now(), status:'queued'});
  return ok('');
};
X['mailq']=function(vm,args){
  var q=mailQ(vm);
  if(!q.length) return ok('Mail queue is empty');
  var out=['-Queue ID-  --Size-- ----Arrival Time---- -Sender/Recipient----','----------- -------- --------------------- ----------------------'];
  q.forEach(function(m,i){
    out.push(new Date(m.ts).toISOString().slice(0,19).replace('T',' ')+'    <'+m.from+'>');
    out.push('            (connect to 127.0.0.1)');
    out.push('                                         '+m.to);
  });
  out.push('-- '+q.length+' Kbytes in '+q.length+' Request(s).');
  return ok(out.join('\n'));
};

/* --- openssl x509 证书检查 --- */
X['openssl-x509']=function(vm,args){ return opensslX509(vm,args); };

function opensslX509(vm,args){
  var file=null, mode=null;
  for(var i=0;i<args.length;i++){
    if(args[i]==='-in') file=args[++i];
    else if(args[i]==='-noout') mode='noout';
    else if(args[i]==='-text') mode='text';
    else if(args[i]==='-subject') mode='subject';
  }
  if(!file) return bad('openssl x509: no -in file specified');
  var pem=vm.read(file);
  if(pem===null) return bad('openssl x509: Could not open file or uri: '+file);
  var s=String(pem);
  if(s.indexOf('-----BEGIN CERTIFICATE-----')<0) return bad('openssl x509: unable to load certificate');
  var subj=(s.match(/Subject:\s*(.+)/)||[,''])[1].trim();
  var issuer=(s.match(/Issuer:\s*(.+)/)||[,''])[1].trim();
  var notAfter=(s.match(/Not After\s*:\s*(.+)/)||[,''])[1].trim();
  if(mode==='subject') return ok('subject='+subj);
  if(mode==='noout') return ok('');
  var out=['subject='+subj,'issuer='+issuer,'notAfter='+notAfter];
  if(s.indexOf('CA:TRUE')>=0) out.push('X509v3 Basic Constraints: critical CA:TRUE');
  if(/X509v3 Subject Alternative Name/.test(s)){
    var san=(s.match(/X509v3 Subject Alternative Name:\s*\n\s*(.+)/)||[,''])[1].trim();
    out.push('X509v3 Subject Alternative Name: \n    '+san);
  }
  if(/TLS Web Server Authentication/.test(s)) out.push('X509v3 Extended Key Usage: TLS Web Server Authentication');
  return ok(out.join('\n'));
}

/* ---------- 评分能力探测（供 competition.js 用） ---------- */
E.extras={
  sysctl: function(vm,key){ var s=sysctlState(vm); return s[key]===undefined?null:String(s[key]); },
  forwarding4: function(vm){ return E.extras.sysctl(vm,'net.ipv4.ip_forward')==='1'; },
  forwarding6: function(vm){ return E.extras.sysctl(vm,'net.ipv6.conf.all.forwarding')==='1'; },
  hasNat:    function(vm){ return E.extras_iptablesHas(vm,'nat','POSTROUTING',function(r){ return /-j (MASQUERADE|SNAT)/.test(r); }).ok; },
  hasPreroute: function(vm){ return E.extras_iptablesHas(vm,'nat','PREROUTING',function(r){ return /-j DNAT/.test(r); }).ok; },
  hasForwardFilter: function(vm){ return E.extras_iptablesHas(vm,'filter','FORWARD',function(r){ return /-j (ACCEPT|DROP|REJECT)/.test(r); }).ok; },
  hasMasqueradeOn: function(vm,ip){ return E.extras_iptablesHas(vm,'nat','POSTROUTING',function(r){ return /-j MASQUERADE/.test(r)&&(!ip||r.indexOf(ip)>=0); }).ok; },
  wg: E.extras_wgState,
  wgUp: function(vm){ var s=vm.svc('wg-quick-wg0'); return !!(s&&s.running); },
  wgHasPSK: function(vm){ var w=E.extras_wgState(vm); return w.peers.some(function(p){ return !!p.psk; }); },
  squid: E.extras_squidParse,
  squidIntercept: function(vm){ var p=E.extras_squidParse(vm); return !!p.intercept; },
  postfix: E.extras_postfixParse,
  mailq: function(vm){ return mailQ(vm).slice(); },
  x509: opensslX509,
  certExists: function(vm,p){ var s=vm.read(p); return !!(s&&String(s).indexOf('-----BEGIN CERTIFICATE-----')>=0); },
  chainText: function(vm,p){ var s=vm.read(p); return s===null?'':String(s); }
};

/* ---------- 把命令并入 CMDS ---------- */
/* 目录不存在时给出与真实系统一致的报错 */
var _w=root.LabEngine;
if(!_w) throw new Error('lab-extras 需要先加载 lab-engine.js');

E.CMDS=E.CMDS||{};
for(var k in X) E.CMDS[k]=X[k];
/* openssl 的 x509 子命令走 dispatch */
var _os=E.CMDS['openssl'];
if(_os){
  E.CMDS['openssl']=function(vm,args){
    if(args[0]==='x509') return opensslX509(vm,args);
    if(args[0]==='req'||args[0]==='genrsa'||args[0]==='genpkey'||args[0]==='verify'||args[0]==='dgst'){
      var st=readOr(vm,'/etc/ssl/openssl.cnf','');
      if(args[0]==='verify') return ok('CN OK');
      if(args[0]==='req'&&(args.indexOf('-newkey')>=0||args.indexOf('-new')>=0)) return ok('Certificate request self-signature ok');
      if(!st) st='[ req ]\ndistinguished_name = req_distinguished_name\n[ req_distinguished_name ]\n';
      return ok('（openssl '+args[0]+' 模拟器：证书生成已简化处理）');
    }
    if(args[0]==='version'||args[0]==='v') return ok('OpenSSL 3.0.2 15 Mar 2022 (Library: OpenSSL 3.0.2)');
    return _os.apply(this,arguments);
  };
}

})(typeof window!=='undefined'?window:(typeof globalThis!=='undefined'?globalThis:this));
