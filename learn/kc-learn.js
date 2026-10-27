/* ============================================================
   知识公社 · 学习引擎 kc-learn.js（v1）
   —— 让静态课程"活"起来：进度 / 小测 / 下一讲 / 继续学习
   ------------------------------------------------------------
   用法（零配置，引入即生效）：
   · 课程页：自动扫描 .lesson 讲卡 → 加完成按钮 + 进度条 + 下一讲
   · 入口页：页面放一个 <div id="kc-resume"></div> → 渲染「继续学习」卡
   数据全部存本机（localStorage），无后端、离线可用。
   ============================================================ */
(function () {
  'use strict';

  var INDEX_KEY = 'kc:index';

  function load(k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function mk(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }

  /* ---------- 引擎样式（自包含注入） ---------- */
  function injectStyle() {
    if (document.getElementById('kc-learn-style')) return;
    var css = [
      '#kc-progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:900;background:transparent;pointer-events:none}',
      '#kc-progress i{display:block;height:100%;width:0;background:linear-gradient(90deg,#b8443c,#9e2b25);transition:width .35s ease}',
      '#kc-fab{position:fixed;right:14px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:900;',
      'border:1.5px solid #9e2b25;background:#fffdf8;color:#7c1f1a;border-radius:12px;',
      'padding:9px 15px;font:14px/1.5 "Songti SC","Noto Serif CJK SC",serif;letter-spacing:1px;text-align:center;',
      'box-shadow:0 5px 18px rgba(80,40,20,.16);cursor:pointer;opacity:0;transform:translateY(6px);',
      'transition:opacity .25s ease,transform .25s ease,background .2s;pointer-events:none}',
      '#kc-fab.on{opacity:1;transform:none;pointer-events:auto}',
      '#kc-fab .kc-fab-n{display:block;font-size:11px;color:#9a927f;letter-spacing:0;margin-bottom:1px}',
      '#kc-fab.done{background:#9e2b25;color:#fdf6ea;border-color:#9e2b25}',
      '#kc-fab.done .kc-fab-n{color:#e8c8a0}',
      '.kc-done{display:inline-block;margin:16px 0 2px;border:1.5px dashed #cbb98f;',
      'background:#fffdf8;color:#7c6a48;border-radius:8px;padding:8px 15px;font:13.5px/1.4 inherit;',
      'cursor:pointer;letter-spacing:1px;transition:border-color .2s,background .2s,color .2s}',
      '.kc-done:hover{border-color:#9e2b25;color:#7c1f1a}',
      '.kc-done.on{border:1.5px solid #4c6b4f;background:#f2f7f0;color:#3c5a3f}',
      '.kc-done[data-s=doing]{border-style:solid;border-color:#c9a227;background:#fdf9ec;color:#8a6d1f}',
      '.kc-done[data-s=skip]{border-style:dotted;border-color:#b9b0a0;background:#f4f2ee;color:#8a8478}',
      '.kc-done .kc-done-hint{display:block;font-size:11px;color:#a89e8c;margin-top:2px;letter-spacing:0}',
      '.lesson[data-s=skip]{opacity:.55}',
      '.qz{border:1px solid #e6dfd0;background:#fffcf5;border-radius:10px;padding:14px 16px;margin:14px 0 6px}',
      '.qz-q{font-weight:700;color:#2b2620;margin-bottom:10px;font-family:"Songti SC","Noto Serif CJK SC",serif}',
      '.qz-o{display:block;width:100%;text-align:left;border:1.5px solid #e6dfd0;background:#fff;border-radius:8px;',
      'padding:10px 13px;margin:7px 0;font:14px/1.6 inherit;color:#4d463c;cursor:pointer;transition:border-color .15s,background .15s}',
      '.qz-o:hover{border-color:#b98b6a}',
      '.qz-o.ok{border-color:#4c6b4f;background:#eef6ec;color:#2f4d33;font-weight:700}',
      '.qz-o.no{border-color:#c0392b;background:#fdf0ee;color:#8c2f24;animation:kc-shake .4s}',
      '@keyframes kc-shake{0%,100%{transform:none}25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}',
      '.qz.done .qz-o{cursor:default;opacity:.92}',
      '.qz-why{margin-top:8px;background:#f6f2e8;border-left:3px solid #a4884a;border-radius:0 8px 8px 0;padding:9px 12px;font-size:13px;color:#5c5344}',
      '.kc-resume-card{display:flex;flex-direction:column;gap:6px;padding:2px}',
      '.kc-r-k{font-size:12px;color:#9e2b25;letter-spacing:4px;font-family:"Songti SC",serif}',
      '.kc-r-t{font-size:16.5px;font-weight:700;font-family:"Songti SC","Noto Serif CJK SC",serif}',
      '.kc-r-bar{display:block;height:6px;background:#efe9dc;border-radius:3px;overflow:hidden;margin-top:2px}',
      '.kc-r-bar i{display:block;height:100%;background:#9e2b25;border-radius:3px}',
      '.kc-resume-empty{color:#7c7466;font-size:14px}',
      '#kc-toast{position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom));transform:translate(-50%,14px);',
      'background:#9e2b25;color:#fdf6ea;border-radius:10px;padding:12px 20px;font:14px/1.6 "Songti SC",serif;',
      'letter-spacing:1px;box-shadow:0 8px 26px rgba(100,40,20,.28);opacity:0;transition:opacity .3s ease,transform .3s ease;z-index:950;',
      'max-width:calc(100vw - 32px);text-align:center;pointer-events:none}',
      '#kc-toast.on{opacity:1;transform:translate(-50%,0)}'
    ].join('');
    var s = mk('style');
    s.id = 'kc-learn-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function toast(msg) {
    var t = document.getElementById('kc-toast');
    if (!t) { t = mk('div'); t.id = 'kc-toast'; document.body.appendChild(t); }
    t.textContent = msg;
    requestAnimationFrame(function () { t.classList.add('on'); });
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.classList.remove('on'); }, 2800);
  }

  /* ============ 模式 A：课程页 ============ */
  var lessons = [].slice.call(document.querySelectorAll('.lesson'));
  if (lessons.length) initCourse();

  function initCourse() {
    injectStyle();
    var fname = location.pathname.split('/').pop() || 'course.html';
    var PKEY = 'kc:course:' + fname;
    var st = load(PKEY, { done: {} });
    if (!st.done) st.done = {};
    st.state = st.state || {};
    for (var _k in st.done) if (st.done[_k] && !st.state[_k]) st.state[_k] = 'done';
    var title = (document.title || '').split('·')[0].trim() || '课程';

    var bar = mk('div'); bar.id = 'kc-progress';
    var barI = mk('i'); bar.appendChild(barI);
    document.body.appendChild(bar);

    var fab = mk('button'); fab.id = 'kc-fab'; fab.type = 'button';
    document.body.appendChild(fab);

    lessons.forEach(function (L, i) {
      if (!L.id) L.id = 'l' + (i + 1);
      var b = mk('button', 'kc-done'); b.type = 'button';
      b.onclick = function () { toggle(L.id); };
      L.appendChild(b);
    });

    /* 重访恢复：已学完的讲，其测验显示为已完成态 */
    lessons.forEach(function (L) {
      if (!st.done[L.id]) return;
      [].slice.call(L.querySelectorAll('.qz')).forEach(function (box) {
        box.dataset.done = '1';
        box.classList.add('done');
        var ok = box.querySelector('.qz-o[data-a="1"]');
        if (ok) ok.classList.add('ok');
        var w = box.querySelector('.qz-why');
        if (w) w.hidden = false;
      });
    });

    function count() { var _n = 0; for (var _k in st.state) if (st.state[_k] === 'done') _n++; return _n; }
    function allDone() { return lessons.length > 0 && count() >= lessons.length; }
    function nextLesson() {
      for (var i = 0; i < lessons.length; i++) { var _s = st.state[lessons[i].id]; if (_s !== 'done' && _s !== 'skip') return lessons[i]; }
      return null;
    }
    function completedToast() { toast('🎉 本册 ' + lessons.length + ' 讲全部学完，厉害！'); }

    function refresh() {
      lessons.forEach(function (L) {
        var b = L.querySelector('.kc-done'); if (!b) return;
        var _st = st.state[L.id] || '';
        b.dataset.s = _st; L.dataset.s = _st;
        b.classList.toggle('on', _st === 'done');
        b.innerHTML = (_st === 'done' ? '✓ 已学完' : _st === 'doing' ? '学习中…' : _st === 'skip' ? '已跳过' : '标记学完这一讲')
          + '<span class="kc-done-hint">点一下切换：学习中 → 已学完 → 跳过</span>';
      });
      barI.style.width = (count() / lessons.length * 100) + '%';
      fab.innerHTML = '<span class="kc-fab-n">进度 ' + count() + '/' + lessons.length + ' 讲</span>' +
        (allDone() ? '继续下一册 →' : '下一讲 ↧');
      fab.classList.toggle('done', allDone());
      save(PKEY, st);
      syncIndex();
    }

    function toggle(id) {
      var cur = st.state[id] || '';
      var nx = cur === '' ? 'doing' : cur === 'doing' ? 'done' : cur === 'done' ? 'skip' : '';
      if (nx) st.state[id] = nx; else delete st.state[id];
      delete st.done[id];
      if (nx === 'done' && allDone()) setTimeout(completedToast, 120);
      if (nx === 'skip') toast('这一讲先跳过。跳过不是欠债，是取舍。');
      refresh();
    }

    fab.onclick = function () {
      var nx = nextLesson();
      if (nx) { nx.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
      var nxt = document.querySelector('.wrap a[href*="2.html"]');
      if (nxt) { location.href = nxt.getAttribute('href'); }
      else { toast('已到最后一讲 ✓'); }
    };

    document.addEventListener('click', function (e) {
      var t = e.target;
      var o = t && t.closest ? t.closest('.qz-o') : null;
      if (!o) return;
      var box = o.closest('.qz');
      if (!box || box.dataset.done) return;
      if (o.dataset.a === '1') {
        o.classList.add('ok');
        box.dataset.done = '1';
        box.classList.add('done');
        var why = box.querySelector('.qz-why'); if (why) why.hidden = false;
        var L = o.closest('.lesson');
        if (L && L.id && st.state[L.id] !== 'done') {
          if (st.state[L.id] !== 'skip') { st.state[L.id] = 'done'; if (allDone()) setTimeout(completedToast, 150); }
          refresh();
        }
      } else {
        o.classList.add('no');
        setTimeout(function () { o.classList.remove('no'); }, 450);
      }
    });

    function onScroll() { fab.classList.toggle('on', window.scrollY > 320); }
    window.addEventListener('scroll', onScroll, { passive: true });
    setTimeout(onScroll, 60);

    function syncIndex() {
      var idx = load(INDEX_KEY, {});
      if (count() === 0) { delete idx[fname]; save(INDEX_KEY, idx); return; }
      var nx = nextLesson();
      idx[fname] = {
        title: title, done: count(), total: lessons.length, ts: Date.now(),
        url: location.pathname, nextId: nx ? nx.id : null
      };
      save(INDEX_KEY, idx);
    }

    refresh();
  }

  /* ============ 模式 B：入口页「继续学习」 ============ */
  var resume = document.getElementById('kc-resume');
  if (resume) {
    injectStyle();
    var idx = load(INDEX_KEY, {});
    var arr = Object.keys(idx).map(function (k) { return idx[k]; })
      .filter(function (v) { return v && v.url && v.total; });
    arr.sort(function (a, b) { return (b.ts || 0) - (a.ts || 0); });
    if (!arr.length) {
      var kcBase = (function () {
        var s = document.currentScript;
        if (!s) { var a = document.getElementsByTagName('script'); s = a[a.length - 1]; }
        try { return new URL('./', s.src).href; } catch (e) { return location.href; }
      })();
      resume.innerHTML = '<div class="kc-resume-empty">还没有学习记录 —— <a href="' + kcBase + 'courses/algo.html">从第一课开始：算法竞赛 · 第 1 讲 →</a></div>';
    } else {
      var it = arr[0];
      /* 老版本记录的是裸文件名（都在 learn/courses/ 下），统一归一到绝对路径 */
      var u = it.url || '';
      if (!/^([a-z]+:)?\//i.test(u)) {
        var bs = document.currentScript;
        if (!bs) { var as = document.getElementsByTagName('script'); bs = as[as.length - 1]; }
        try { u = new URL('courses/' + u, bs.src).href; } catch (e) {}
      }
      var link = u + (it.nextId ? '#' + it.nextId : '');
      var pct = Math.round(it.done / it.total * 100);
      resume.innerHTML =
        '<div class="kc-resume-card">' +
        '<span class="kc-r-k">继续学习</span>' +
        '<a class="kc-r-t" href="' + link + '">' + it.title + ' · 已学 ' + it.done + '/' + it.total + ' 讲 →</a>' +
        '<span class="kc-r-bar"><i style="width:' + pct + '%"></i></span>' +
        '</div>';
    }
  }
})();
