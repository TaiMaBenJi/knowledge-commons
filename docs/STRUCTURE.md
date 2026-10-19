# 仓库结构契约（STRUCTURE）

> 2026-10-16 整理。规则只有一条：**页面归页面、数据归数据、产物归产物、工具归工具**。
> 新增东西时按这张表落位；要动目录，先读本文件的「硬约束」。

## 一、顶层分工

| 目录 / 文件 | 放什么 | 不放什么 |
|---|---|---|
| `index.html` | 门户首页 | 别的页面都别学它往根目录堆 |
| `library.html` | 资源总库（全网免费学习资源精选，数据内联） | |
| `study.html` | 资料中心单文件应用（数据外置到 `study-data/`） | |
| `download.html` `install.html` `viewer.html` | 下载页 / 直装页 / 文档阅读器 | |
| `404.html` `sitemap.xml` `robots.txt` | 站点配套（旧链接跳转、收录、爬虫） | |
| `cc59a7f8471abb6edf87c7919a17baff.txt` | IndexNow 站点验证文件（文件名＝密钥，内容同密钥）——**别删、别改名** | |
| `manifest.json` `sw.js` `sw-reg.js` `install-tip.js` | PWA 三件套 | |
| `learn/` | **全部学习页面** | 不放数据、不放视频 |
| `multiskill/` | 世赛 50 赛项学习包（总纲 / 总纲课 / 模拟训练 / 图解） | |
| `videos/` | 视频课与封面（见 `videos/README.md`，**布局是构建契约**） | |
| `docs/` | 文档资料（课程文档 / 官方资料 / 研究文档 / 截图） | 不放页面入口 |
| `study-data/` | 资料中心的数据分块（生成物） | 手改 |
| `learn/files/` `learn/data/` `exam/` `aws-educate/` | 原始资料与源数据 | |
| `lab/` | 云计算实训沙箱（引擎 + 场景 + `standalone.html`），被 `learn/cloud/lab.html` 与门户数据引用 | 不放别的实验 |
| `video-ext/` | 逐集图解册读物（`tools/build_liquid.py` 的输入之一） | |
| `app/` `assets/` `icons/` | 站点资源（门户数据 / 截图 / PWA 图标） | |
| `clients/` | 六端客户端工程（android / ios / windows / macos / linux） | 不放内容 |
| `tools/` | 构建与质检脚本（见 `tools/README.md`） | |
| `video-factory/` | 视频课生成流水线（脚本 + 课件源） | |
| `.github/workflows/` | CI（六端构建 / iOS 签名 / 链接体检 / 视频落位） | |

## 二、learn/ 页面地图

```
learn/
├── index.html          门户
├── archive.html        总目：全站一页直达
├── search.html         全站检索（数据：searchidx.js）
├── paths.html          四条「从零到精通」学习路线
├── courses.html        课程总览      skills.html   世赛总览
├── contest.html        竞赛题库      exams.html → exam/
├── beginner.html       零基础学堂（15 集视频课）
├── sleep.html          睡前故事考场  ecommerce.html 电商实战中心
├── about.html          关于
├── cloud/              云计算：index(备战中心) lab(实训) week1 4weeks net sprint books(备赛书单) certs(认证地图)
├── courses/            原创课程：algo algo2 python gongkao aws-educate aws-educate-catalog
├── exam/               考试：index 导航 / quiz 自测 / gongkao 公考 / calendar 考试日历 / guofang 国防教育刷题
├── media/              视频馆 wsvideos / B 站精选视频库 bilibili / 文档阅读 pdfview
├── red/                红色经典：index(入口) maoxuan(毛选全文) socialism(社会主义实践研究)
├── dev/                开发者免费服务总表（整合 ripienaar/free-for-dev；页面 index.html + 数据 ffd-data.js）
├── files/              课程与题库原始资料（730 份，仅被页面按需引用）
├── data/               学习引擎数据
└── style.css  kc-learn.js  kc-srs.js  searchidx.js
```

导航栏在所有页面里是**复制的同一段**（无构建步骤，纯静态）。改导航 = 批量改 `learn/*.html` 与子目录页面，
注意相对路径：根页用 `cloud/index.html`，子目录页用 `../cloud/index.html`。

## 三、硬约束（动目录前必读）

1. **`videos/` 与 `multiskill/` 的相对路径被客户端与工作流硬编码**
   - `.github/workflows/embed-course-videos.yml` 明确 `ls videos/*.mp4`、`videos/course/*.mp4`
   - `viewer.html` 对 `src` 以 `videos/` 开头的路径原样保留
   - `clients/*/build_ci.sh` 整目录 `cp -R videos/`
   → **不要重排 `videos/` 下的层级**，只往里加文件。
2. **`multiskill/**/{总纲课.mp4,模拟训练.html,项目总纲.md}` 三件套命名**
   由 `learn/media/wsvideos.html`、`learn/skills.html`、`app/portal-trades.js` 以 URL 编码路径引用，改名要三处同改。
3. **`study-data/` 是生成物**：由 `tools/build_liquid.py` + `tools/split_study.py` 产出。
   改完内容数据要同步 bump `sw.js` 的 `VERSION`。
4. **PWA 预缓存清单在 `sw.js`**：新增/移动页面后必须更新，否则离线用户拿不到新页。
5. **旧路径兼容**：2026-10-16 的 `learn/` 目录整理使用 `404.html` 内的映射表做跳转，
   新增映射时把 `旧路径 → 新路径` 追加进 `404.html` 的 `MAP`。

## 四、新增一页的标准动作

1. 页面落到对应子目录（见上面地图），别堆在 `learn/` 根。
2. 页面导航片段复制同目录邻居的写法，改相对路径。
3. 把 URL 加进 `sitemap.xml` 与 `sw.js` 的预缓存清单；检索内容加进 `learn/searchidx.js`。
4. 若有新目录，同步更新本文件与 `README.md` 的仓库地图。
