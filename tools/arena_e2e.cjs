/* arena.html 端到端测试（需 jsdom）
   跑法： npm i jsdom && node tools/arena_e2e.cjs
   验证：引擎加载 / 落地页渲染 / 进场景 / 敲命令 / 评分面板 / 限时开考 / 倒计时走动 / 完全自包含
*/
/* End-to-end test: load learn/arena.html in jsdom, drive the real UI. */
const fs = require("fs");
const path = require("path");
(async function(){
  let JSDOM;
try { JSDOM = require("jsdom").JSDOM; }
catch (e) {
  console.error("缺少依赖 jsdom。请先执行：  npm i jsdom");
  console.error("然后：               node tools/arena_e2e.cjs");
  process.exit(2);
}

  const FILE = "/workspace/kc/learn/arena.html";
  let fail = 0;
  const ok = (c, m) => { console.log((c ? "  ✅ " : "  ❌ ") + m); if (!c) fail++; };

  console.log("=== 1. 加载页面 ===");
  const html = fs.readFileSync(FILE, "utf8");
  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    pretendToBeVisual: true,
    url: "https://example.com/learn/arena.html",
  });
  const { window } = dom;
  const doc = window.document;
  // jsdom lacks a few things the UI touches
  window.HTMLElement.prototype.scrollIntoView = function () {};
  window.navigator.vibrate = function () {};
  if (!window.matchMedia) window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });

  await new Promise((r) => setTimeout(r, 900));

  console.log("=== 2. 引擎加载 ===");
  ok(!!window.LabEngine, "LabEngine 存在");
  ok(!!window.LabUI, "LabUI 存在");
  ok(window.LabEngine.SCENARIOS.length === 22,
     `场景数 = ${window.LabEngine.SCENARIOS ? window.LabEngine.SCENARIOS.length : "?"}（期望 22）`);
  ok((window.LabEngine.EXAM_PAPERS || []).length === 4,
     `试卷数 = ${(window.LabEngine.EXAM_PAPERS || []).length}（期望 4）`);
  ok(window._labUIBound === 1, `UI 已绑定到 DOM（_labUIBound=${window._labUIBound}）`);
  if (window._labInitErr) { console.log("     initErr: " + window._labInitErr); fail++; }

  console.log("=== 3. 落地页渲染 ===");
  const papers = doc.querySelectorAll("#papers [data-exam]");
  ok(papers.length === 4, `试卷卡片渲染 ${papers.length} 张（期望 4）`);
  const scns = doc.querySelectorAll("#scnList [data-scn]");
  ok(scns.length === 22, `场景入口渲染 ${scns.length} 个（期望 22）`);
  const titles = [...papers].map((b) => b.closest(".paper").querySelector(".pn").textContent);
  console.log("     试卷：" + titles.join(" / "));
  const firstScn = doc.querySelector("#scnList li .t").textContent.replace(/\s+/g," ").trim().slice(0,60);
  console.log("     首个场景：" + firstScn);
  ok(!doc.getElementById("err").style.display.includes("block"), "无引擎错误提示");

  console.log("=== 4. 进入场景（不限时）===");
  doc.getElementById("goLab").click();
  await new Promise((r) => setTimeout(r, 400));
  const tv = doc.getElementById("termView");
  ok(tv.classList.contains("on"), "终端已打开");
  const scr = doc.getElementById("tvScr").textContent;
  ok(scr.length > 20, "终端有输出：" + JSON.stringify(scr.slice(-70)));
  const title = doc.getElementById("tvTitle").textContent;
  ok(!!title, "场景标题：" + title);

  console.log("=== 5. 敲真实命令 ===");
  const inp = doc.getElementById("tvIn");
  function run(cmd) {
    inp.value = cmd;
    const ev = new window.KeyboardEvent("keydown", { key: "Enter", bubbles: true });
    inp.dispatchEvent(ev);
  }
  const before = doc.getElementById("tvScr").textContent;
  run("whoami");
  await new Promise((r) => setTimeout(r, 200));
  const after = doc.getElementById("tvScr").textContent;
  ok(after !== before, "命令产生了输出");
  ok(after.indexOf("root") >= 0 || after.indexOf("whoami") >= 0, "whoami 返回了合理内容");
  console.log("     终端尾部：" + JSON.stringify(after.slice(-90)));

  console.log("=== 6. 评分面板 ===");
  doc.getElementById("tvGradeBtn").click();
  await new Promise((r) => setTimeout(r, 300));
  const panel = doc.getElementById("tvPanel");
  ok(panel.classList.contains("on"), "评分面板已打开");
  console.log("     评分面板：" + JSON.stringify(panel.textContent.replace(/\s+/g, " ").slice(0, 90)));

  console.log("=== 7. 限时模拟赛（mini）===");
  doc.getElementById("tvBack").click();
  await new Promise((r) => setTimeout(r, 300));
  doc.getElementById("goExam").click();
  await new Promise((r) => setTimeout(r, 400));
  ok(doc.getElementById("tvConfirm").classList.contains("on"), "弹出开考确认框");
  doc.getElementById("tvConfirmYes").click();
  await new Promise((r) => setTimeout(r, 600));
  const exam=window.LabUI._S.exam;
  ok(!!exam, "考试状态已建立，剩余秒数="+(exam&&exam.left)+"（期望 1800 = 30 分钟）");
  ok(doc.getElementById("labView").classList.contains("on"), "考试面板已打开");
  const clock=doc.getElementById("examClock");
  ok(!!clock, "倒计时时钟已渲染："+(clock&&clock.textContent));
  ok(clock && /^\d\d:\d\d$/.test(clock.textContent.trim()), "倒计时格式正确："+(clock&&clock.textContent));
  const taskBtns=doc.querySelectorAll("#labBody [data-open], #labBody [data-task], #labBody .qz-item button");
  console.log("     考试面板任务按钮："+taskBtns.length+" 个");
  ok(taskBtns.length>0, "任务清单可点击");
  if(taskBtns.length){
    taskBtns[0].click();
    await new Promise((r) => setTimeout(r,500));
    ok(tv.classList.contains("on"), "从考试面板进入任务，终端已打开");
    const t2=doc.getElementById("tvTitle").textContent;
    ok(!!t2, "任务标题："+t2);
    const tc=doc.getElementById("tvExamClock");
    ok(!!tc, "终端标题栏已注入倒计时："+(tc?tc.textContent:"<无>"));
    if(tc){
      const t1=tc.textContent;
      ok(/⏱\s*\d\d:\d\d/.test(t1), "倒计时在跑："+t1);
      await new Promise((r)=>setTimeout(r,2200));
      ok(tc.textContent!==t1, "倒计时在走动："+t1+" -> "+tc.textContent);
      console.log("     标题栏样式色："+(tc.style.color||"(未设)")+"  背景："+(tc.style.background||"(未设)"));
    }
  }

  console.log("=== 8. 离线自包含 ===");
  ok(!/<script[^>]+src=/.test(html), "没有任何外部 <script src>（完全自包含）");
  ok(!/<link[^>]+stylesheet/.test(html.replace(/<link rel="manifest"[^>]*>/, "")),
     "没有外部 CSS 依赖（lab.css 已内联）");
  ok(html.indexOf("LabEngine") > 0 && html.indexOf("EXAM_PAPERS") > 0, "引擎与试卷定义内联在页面里");

  console.log("");
  console.log("=".repeat(56));
  console.log(fail === 0 ? "端到端测试：全部通过 ✅" : `端到端测试：${fail} 项失败 ❌`);
  process.exit(fail ? 1 : 0);

})();
