/* 知识公社 · Service Worker 注册器
   自定位：sw.js 与本脚本同目录（仓库根），任何深度的页面均可引用本文件。 */
(function () {
  /* file:// 直开检测：浏览器安全策略会禁掉 Service Worker 与跨文件 fetch，
     检索 / 离线 / 视频 / PDF 等功能必然失灵——与其让用户面对「全是坏的」，
     不如一条横幅讲清楚正确打开方式 */
  if (location.protocol === 'file:') {
    var b = document.createElement('div');
    b.setAttribute('style', 'position:fixed;left:12px;right:12px;bottom:12px;z-index:99999;' +
      'background:#9e2b25;color:#fff;padding:14px 16px;border-radius:12px;font:14px/1.7 system-ui,' +
      '"Noto Sans SC",sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.35);max-width:640px;margin:0 auto');
    b.innerHTML = '<b>检测到直接打开了本地文件</b><br>' +
      '浏览器安全限制会让本页的检索、离线、视频、PDF 等功能不可用。请改用：' +
      '<a href="https://taimabenji.github.io/knowledge-commons/learn/" style="color:#ffd9a0">网页版</a>（可安装为 App），' +
      '或到 <a href="https://taimabenji.github.io/knowledge-commons/download.html" style="color:#ffd9a0">下载页</a> 获取各端安装包。' +
      '<span id="kc-fileclose" style="float:right;cursor:pointer;opacity:.8;padding:0 6px">✕</span>';
    (document.body || document.documentElement).appendChild(b);
    var x = document.getElementById('kc-fileclose');
    if (x) x.onclick = function () { b.remove(); };
    return;
  }
  if (!('serviceWorker' in navigator)) return;
  var s = document.currentScript;
  if (!s) {
    var all = document.getElementsByTagName('script');
    s = all[all.length - 1];
  }
  if (!s || !s.src) return;
  var swUrl;
  try { swUrl = new URL('sw.js', s.src).href; } catch (e) { return; }
  window.addEventListener('load', function () {
    navigator.serviceWorker.register(swUrl).catch(function () { /* 静默：SW 不可用不影响阅读 */ });
  });
})();
