/* =====================================================================
   competition-ui.js · 竞赛仿真场界面
   ------------------------------------------------------------
   依赖：lab-engine.js + lab-extras.js + lab-scenarios.js + competition.js
   · 赛事选择（5 项：世赛里昂 / 世赛上海 / 省赛 / 金砖 / 国赛私有云）
   · 赛程与模块权重展示
   · 任务清单（官方 task 编号 + 分值 + 实时勾选）
   · 限时计时、交卷、成绩报告（总分 / 模块分布 / 失分点 / WSOS 对照）
   ===================================================================== */
(function(root){
'use strict';
var E=root.LabEngine;
if(!E||!E.COMPETITIONS) return;
if(typeof document==='undefined') return;

var S={ comp:null, timer:null, tab:'A' };

function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function $(id){ return document.getElementById(id); }
function fmtT(sec){ sec=Math.max(0,sec|0); var m=Math.floor(sec/60), s=sec%60; return (m<10?'0':'')+m+':'+(s<10?'0':'')+s; }
function LS(k,d){ try{ var v=localStorage.getItem(k); return v?JSON.parse(v):d; }catch(e){ return d; } }
function LSset(k,v){ try{ localStorage.setItem(k,JSON.stringify(v)); }catch(e){} }
function toast(m){ if(root.toast) { try{ root.toast(m); return; }catch(e){} } var t=$('tvToast'); if(t){ t.textContent=m; t.classList.add('on'); setTimeout(function(){t.classList.remove('on');},2200); } }

/* ---------- 虚拟盘：每场赛事一台独立 VM ---------- */
function vmKey(cid){ return 'kc.comp.vm.'+cid; }
function getVM(cid){
  if(!E._compVMs) E._compVMs={};
  if(E._compVMs[cid]) return E._compVMs[cid];
  var json=LS(vmKey(cid),null);
  var vm;
  if(json && E.vmFromJSON){ try{ vm=E.vmFromJSON(json); }catch(e){ vm=null; } }
  if(!vm){ vm=E.newVM(cid); E.compSetup(vm,cid); }
  if(!vm.compProg){ vm.compProg=LS('kc.comp.prog.'+cid,{}); }
  E._compVMs[cid]=vm;
  return vm;
}
function saveVM(cid){
  if(!E._compVMs||!E._compVMs[cid]||!E.vmToJSON) return;
  try{ LSset(vmKey(cid), E.vmToJSON(E._compVMs[cid])); LSset('kc.comp.prog.'+cid, E._compVMs[cid].compProg||{}); }catch(e){}
}

/* ---------- 赛事选择 ---------- */
function renderPicker(){
  var list=E.competitionList();
  var h='<div class="qz-item"><h4>🏟 选一场比赛开始</h4>'+
    '<p class="lab-sub">每场赛事一台独立虚拟服务器，进度自动保存本机，随时可以中断回来继续。</p></div>';
  list.forEach(function(c){
    var prog=LS('kc.comp.prog.'+c.id,{});
    var done=Object.keys(prog).filter(function(k){return prog[k]>=100;}).length;
    h+='<div class="qz-item comp-card" data-comp="'+esc(c.id)+'">'+
      '<div style="display:flex;align-items:center;gap:10px">'+
        '<span class="pill" style="margin:0;padding:1px 9px;font-size:11.5px">'+esc(c.level)+'</span>'+
        '<b style="flex:1;font-size:15.5px">'+esc(c.name)+'</b></div>'+
      '<p class="lab-sub" style="margin:6px 0 0">'+esc(c.sub)+'</p>'+
      '<p class="lab-sub" style="margin:4px 0 0;color:#8b949e">'+c.days+' 天 · 总时长 '+fmtT(c.totalMin*60)+
        ' · '+c.modules+' 模块 · '+c.taskCount+' 项'+(done?(' · 已完成 '+done+' 项'):'')+'</p></div>';
  });
  return h;
}

/* ---------- 赛事主视图 ---------- */
function renderComp(){
  var cid=S.comp, c=E.competitionById(cid);
  if(!c) return renderPicker();
  var vm=getVM(cid), rep=E.compGrade(vm,cid);
  var m=null;
  rep.modules.forEach(function(x){ if(x.id===S.tab) m=x; });
  if(!m) { m=rep.modules[0]; S.tab=m.id; }
  var left=LS('kc.comp.left.'+cid,null);
  var h='';
  /* 头部 */
  h+='<div class="qz-item"><div style="display:flex;align-items:center;gap:10px">'+
     '<div style="flex:1"><h4 style="margin:0">🏟 '+esc(c.name)+'</h4>'+
     '<div class="lab-sub">'+esc(c.sub)+'</div></div>'+
     (left!=null? '<div class="exam-clock" id="compClock">'+fmtT(left)+'</div>' : '')+
     '</div>'+
     '<div class="lab-sub" style="margin-top:8px">总时长 '+fmtT(c.totalMin*60)+' · '+c.days+' 天 · 加权得分 <b>'+rep.weighted+'</b> / 100 · 原始得分 '+rep.total+' / '+rep.full+'</div>'+
     '<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">'+
       '<button class="qz-btn" data-act="tickbook" style="margin:0;padding:7px 13px">📋 生成题书</button>'+
       '<button class="qz-btn ghost" data-act="timer" style="margin:0;padding:7px 13px">⏱ '+(left!=null?'暂停计时':'开始计时')+'</button>'+
       '<button class="qz-btn ghost" data-act="report" style="margin:0;padding:7px 13px">📊 成绩报告</button>'+
       '<button class="qz-btn ghost" data-act="reset" style="margin:0;padding:7px 13px">↺ 重置本场</button>'+
     '</div></div>';
  /* 要点 */
  if(c.notes&&c.notes.length){
    h+='<div class="qz-item"><h4>📌 本场要点</h4><ul class="lab-sub" style="margin:4px 0 0;padding-left:18px">'+
      c.notes.map(function(n){return '<li>'+esc(n)+'</li>';}).join('')+'</ul></div>';
  }
  /* 模块切换 */
  h+='<div class="qz-item"><h4>模块与权重</h4><div class="chips">';
  rep.modules.forEach(function(x){
    h+='<button class="chip'+(x.id===S.tab?' on':'')+'" data-tab="'+esc(x.id)+'">'+esc(x.name)+
       ' <b>'+x.got+'/'+x.sum+'</b> · 权重'+x.w+'%</button>';
  });
  h+='</div></div>';
  /* 当前模块 */
  h+='<div class="qz-item"><h4>'+esc(m.name)+'　建议用时 '+m.mins+' 分钟　得分 '+m.got+' / '+m.sum+'（'+m.pct+'%）</h4>';
  m.groups.forEach(function(g){
    if(g.host){
      h+='<div style="margin-top:12px"><b style="font-size:14px">'+esc(g.id)+' · '+esc(g.t)+'</b>'+
         '<p class="lab-sub">该模块为 Windows 侧清单，共 '+g.sum+' 项，仿真器以自评勾选为准。</p>';
      h+='<div class="checklist">';
      g.checklist.forEach(function(it,i){
        var k='hc_'+g.id+'_'+i, done=!!(vm.compProg[cid]&&vm.compProg[cid][k]);
        h+='<label class="cl"><input type="checkbox" data-hc="'+esc(k)+'"'+(done?' checked':'')+'><span>'+esc(it)+'</span></label>';
      });
      h+='</div></div>';
      return;
    }
    h+='<div style="margin-top:12px"><b style="font-size:14px">'+esc(g.id)+' · '+esc(g.t)+
       '　<span style="color:#8b949e;font-size:12px">'+g.got+'/'+g.sum+'（'+g.pct+'%）</span></b></div>';
    h+='<div class="clist">';
    g.tasks.forEach(function(t){
      h+='<div class="cl-row'+(t.ok?' ok':'')+'">'+
         '<span class="cl-id">'+esc(t.id)+'</span>'+
         '<span class="cl-d">'+esc(t.d)+(t.msg?'<em>'+esc(t.msg)+'</em>':'')+'</span>'+
         '<span class="cl-p">'+t.p+'</span>';
      if(t.scn) h+='<button class="cl-go" data-scn="'+esc(t.scn)+'" data-tid="'+esc(t.id)+'">进入实训</button>';
      h+='</div>';
    });
    h+='</div>';
  });
  h+='</div>';
  return h;
}

/* ---------- 成绩报告 ---------- */
function renderReport(){
  var cid=S.comp, vm=getVM(cid), rep=E.compGrade(vm,cid);
  var h='<div class="qz-item"><h4>📊 '+esc(rep.comp.name)+' · 成绩报告</h4>'+
    '<div class="bigscore">'+rep.total+'<span>/'+rep.full+'</span></div>'+
    '<p class="lab-sub">原始得分率 '+rep.pct+'% · 按模块权重折算 <b>'+rep.weighted+' / 100</b></p></div>';
  h+='<div class="qz-item"><h4>模块分布</h4><div class="bars">';
  rep.modules.forEach(function(m){
    h+='<div class="bar-row"><span class="bl">'+esc(m.name)+'</span>'+
      '<span class="bt"><i style="width:'+m.pct+'%"></i></span>'+
      '<span class="bv">'+m.got+'/'+m.sum+' · 权重'+m.w+'%</span></div>';
  });
  h+='</div></div>';
  var lost=[];
  rep.modules.forEach(function(m){ m.groups.forEach(function(g){ (g.tasks||[]).forEach(function(t){
    if(!t.ok) lost.push({m:m.name,g:g.t,t:t}); }); }); });
  h+='<div class="qz-item"><h4>❌ 失分点（'+lost.length+'）</h4>';
  if(!lost.length) h+='<p class="lab-sub">全部达标。</p>';
  lost.slice(0,60).forEach(function(x){
    h+='<div class="lost"><span class="cl-id">'+esc(x.t.id)+'</span>'+
       '<span class="cl-d">'+esc(x.t.d)+'<em>'+esc(x.t.msg||'')+'</em></span>'+
       '<span class="cl-p">-'+x.t.p+'</span></div>';
  });
  if(lost.length>60) h+='<p class="lab-sub">… 另有 '+(lost.length-60)+' 项</p>';
  h+='</div>';
  var w=E.compWsosMap(cid,rep);
  if(w){
    h+='<div class="qz-item"><h4>📐 WSOS 2026 八项权重对照（自评参考）</h4><div class="bars">';
    w.forEach(function(x){
      h+='<div class="bar-row"><span class="bl">'+esc(x.k)+'</span>'+
        '<span class="bt"><i style="width:'+Math.round(x.weight*100/25)+'%"></i></span>'+
        '<span class="bv">官方权重 '+x.weight+'% · 折算估计 '+x.est+'</span></div>';
    });
    h+='</div><p class="lab-sub">WSOS 为官方职业标准的八项权重；「折算估计」按本场加权得分线性映射，仅供自评参考，不是官方评分。</p></div>';
  }
  return h;
}

/* ---------- 计时 ---------- */
function toggleTimer(){
  var cid=S.comp;
  var left=LS('kc.comp.left.'+cid,null);
  if(left==null){
    var c=E.competitionById(cid);
    var mins=Math.round(c.totalMin/Math.max(1,c.modules.length));
    left=mins*60;
    startTimer();
  } else { stopTimer(); left=null; }
  LSset('kc.comp.left.'+cid,left);
  paint();
}

/* ---------- 事件绑定 ---------- */
var BOUND=false;
function bind(){
  var body=$('labBody'); if(!body||BOUND) return;
  BOUND=true;
  body.addEventListener('click',function(e){
    var card=e.target.closest('[data-comp]');
    if(card){ S.comp=card.getAttribute('data-comp'); S.tab=null; saveVM(S.comp); paint(); return; }
    var tab=e.target.closest('[data-tab]');
    if(tab){ S.tab=tab.getAttribute('data-tab'); paint(); return; }
    var scn=e.target.closest('[data-scn]');
    if(scn){
      var tid=scn.getAttribute('data-tid'), id=scn.getAttribute('data-scn');
      try{ E.LabUI.openScenario(id, false, function(pct){ E.compRecord(getVM(S.comp),S.comp,tid,pct); saveVM(S.comp); paint(); toast('已记录 '+tid+'：'+pct+'%'); }); }
      catch(err){ toast('打开实训失败：'+err.message); }
      return;
    }
    var act=e.target.closest('[data-act]');
    if(!act) return;
    var a=act.getAttribute('data-act');
    if(a==='timer') toggleTimer();
    else if(a==='report'){ $('labBody').innerHTML=renderReport(); bindReportBack(); }
    else if(a==='tickbook'){
      var vm=getVM(S.comp);
      toast('题书已生成：/root/TASKBOOK.md（cat 查看）');
    }
    else if(a==='reset'){
      delete E._compVMs[S.comp];
      try{ localStorage.removeItem(vmKey(S.comp)); localStorage.removeItem('kc.comp.prog.'+S.comp); localStorage.removeItem('kc.comp.left.'+S.comp); }catch(e){}
      stopTimer(); toast('本场已重置'); paint();
    }
  });
  body.addEventListener('change',function(e){
    var cb=e.target.closest('[data-hc]');
    if(cb){
      var vm=getVM(S.comp), k=cb.getAttribute('data-hc');
      vm.compProg=S.comp&&E.compProg(vm,S.comp);
      var r=vm.compProg[S.comp]||(vm.compProg[S.comp]={});
      r[k]=cb.checked?100:0;
      saveVM(S.comp); toast(cb.checked?'已勾选':'已取消');
    }
  });
}
function bindReportBack(){
  var b=$('lvBackReport');
  if(b) b.addEventListener('click',function(){ paint(); });
}

/* ---------- 计时器 ---------- */
function startTimer(){
  if(S.timer) return;
  S.timer=setInterval(function(){
    var left=LS('kc.comp.left.'+S.comp,null);
    if(left==null||left<=0){ stopTimer(); if(left!=null) toast('⏰ 时间到 —— 建议立即交卷'); return; }
    left--; LSset('kc.comp.left.'+S.comp,left);
    var el=$('compClock'); if(el) el.textContent=fmtT(left);
    if(left%5===0) saveVM(S.comp);
  },1000);
}
function stopTimer(){ if(S.timer){ clearInterval(S.timer); S.timer=null; } }
function paint(){
  var body=$('labBody'); if(!body) return;
  body.innerHTML=S.comp?renderComp():renderPicker();
  saveVM(S.comp);
}

/* ---------- 对外 API ---------- */
root.CompUI={
  open:function(){
    var lv=$('labView'); if(lv) lv.classList.add('on');
    bind(); paint();
  },
  set:function(cid){ S.comp=cid; S.tab=null; paint(); },
  reset:function(){ S.comp=null; paint(); },
  report:function(){ return S.comp?E.compGrade(getVM(S.comp),S.comp):null; },
  _S:S
};
/* 恢复计时 */
(function(){
  var cid=LS('kc.comp.active',null);
  if(cid && E.competitionById(cid) && LS('kc.comp.left.'+cid,null)!=null){
    S.comp=cid; startTimer();
  }
})();

})(typeof window!=='undefined'?window:(typeof globalThis!=='undefined'?globalThis:this));
