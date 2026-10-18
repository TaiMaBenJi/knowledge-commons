/* ============================================================
   知识公社 · Service Worker（离线可用 + 内容保鲜）
   ------------------------------------------------------------
   策略：
   · 核心页预缓存（install 时）—— 首次打开后即可全站离线；
   · 页面（导航请求）network-first —— 在线永远最新，离线自动回落缓存；
   · 静态资源 stale-while-revalidate —— 秒开 + 后台静默更新；
   · Range 请求 / 非本站请求 —— 直接放行（视频流式播放不受影响）。
   ============================================================ */
var VERSION = 'kc-v1.9.4';
/* 预缓存：主站全部页面 + 样式 + 检索索引 + PWA 资产（≈300KB）
   注：study.html 已拆分（manifest + 58 个按组内容块），本体仅 ~757KB，
   study-data/* 走运行时缓存（首次在线访问后离线可用），不进预缓存清单 */
var CORE = [
  './', './learn/', './study.html',
  './learn/index.html', './learn/archive.html', './learn/courses.html',
  './learn/contest.html', 'learn/exam/index.html', 'learn/exam/gongkao.html',
  './learn/skills.html', 'learn/red/index.html', 'learn/red/socialism.html', './learn/ecommerce.html', 'learn/cloud/index.html', 'learn/cloud/lab.html', 'learn/cloud/week1.html', 'learn/cloud/books.html', 'learn/cloud/certs.html', 'learn/media/wsvideos.html', './learn/sleep.html', './learn/paths.html','./learn/cloud/contest/index.html', './learn/cloud/contest/sim.html','./learn/cloud/start.html','./learn/cloud/contest/data/wsc2026.js', './learn/cloud/contest/data/korea2025.js','./learn/cloud/contest/data/nation.js', './learn/cloud/contest/data/guangdong.js','./learn/cloud/contest/data/brics.js', './learn/cloud/contest/data/wsjobs.js','./learn/media/videos-cloud.html', './learn/media/course-videos.html', './learn/media/data/course-scripts.js',
  './learn/about.html', './learn/beginner.html', 'learn/exam/calendar.html', 'learn/exam/quiz.html', './learn/search.html', 'learn/media/pdfview.html',
  'learn/media/bilibili.html', 'learn/exam/guofang.html',
  'learn/courses/algo.html', 'learn/courses/algo2.html',
  'learn/courses/python.html', 'learn/courses/gongkao.html',
  './learn/red/poems.html',
  './learn/style.css', './learn/searchidx.js', './learn/kc-learn.js',
  './library.html', './app/library-data.js',
  './download.html',
  './install.html',
  './manifest.json',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'
];
var OFFLINE_FALLBACK = './learn/index.html';

self.addEventListener('install', function (e) {
  e.waitUntil((async function () {
    var c = await caches.open(VERSION);
    /* 单条失败不影响整体（addAll 会因任一 404 全失败） */
    await Promise.all(CORE.map(function (u) {
      return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', function (e) {
  e.waitUntil((async function () {
    var ks = await caches.keys();
    await Promise.all(ks.map(function (k) { return k === VERSION ? null : caches.delete(k); }));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  var url;
  try { url = new URL(req.url); } catch (err) { return; }
  if (url.origin !== self.location.origin) return;      /* 第三方直过 */
  if (req.headers.get('range')) return;                 /* 视频等 Range 直过 */

  var isDoc = req.mode === 'navigate' ||
    ((req.headers.get('accept') || '').indexOf('text/html') >= 0);

  if (isDoc) {
    /* 页面：网络优先，离线回落缓存 */
    e.respondWith((async function () {
      try {
        var res = await fetch(req);
        if (res && res.status === 200) {
          var copy = res.clone();
          caches.open(VERSION).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      } catch (err) {
        var hit = await caches.match(req);
        if (hit) return hit;
        var fb = await caches.match(OFFLINE_FALLBACK);
        if (fb) return fb;
        return new Response('离线 · 请联网后重试', {
          status: 503, headers: { 'Content-Type': 'text/plain;charset=utf-8' }
        });
      }
    })());
    return;
  }

  /* 静态资源：缓存优先 + 后台更新 */
  e.respondWith((async function () {
    var hit = await caches.match(req);
    var fetching = fetch(req).then(function (res) {
      if (res && res.status === 200 && res.type === 'basic') {
        var copy = res.clone();
        caches.open(VERSION).then(function (c) { c.put(req, copy); }).catch(function () {});
      }
      return res;
    }).catch(function () { return hit; });
    return hit || fetching;
  })());
});
