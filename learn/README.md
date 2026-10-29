# learn/ —— 学习门户（只放页面）

入口：`index.html`（从仓库根 `index.html` 或直接访问 `/learn/` 进入）。
所有页面共用 `style.css`，没有构建步骤——导航栏是每页各写一遍的静态片段。

## 页面地图

| 路径 | 是什么 |
|---|---|
| `index.html` | 门户首页：全部板块入口 |
| `archive.html` | 总目：站内全库一页直达 |
| `search.html` | 全站检索（索引在 `searchidx.js`，离线可用） |
| `paths.html` | 七条「从零到精通」学习路线（云计算 / 算法竞赛 / 公务员 / 专升本 / 高考 / 全球学术 / 免费认证） |
| `courses.html` | 课程总览 |
| `skills.html` | 世界技能大赛总览（50 赛项三件套直达） |
| `contest.html` | 竞赛题库（Codeforces / AtCoder / ICPC / 蓝桥杯 / 天梯赛） |
| `beginner.html` | 零基础学堂：15 集视频课 + 讲义 |
| `sleep.html` | 云计算睡前故事考场（14 夜故事 + 次日随机考） |
| `ecommerce.html` | 电商创业实战中心 |
| `about.html` | 关于本站 |
| `cloud/index.html` | 云计算 · 世赛备战中心 |
| `cloud/lab.html` | 云计算 · 实战训练场（L1–L4 关卡 + 自动评分） |
| `cloud/week1.html` `cloud/4weeks.html` | 一周入门 / 四周计划 |
| `cloud/net.html` `cloud/sprint.html` | 网络专项 / 冲刺手册 |
| `courses/algo.html` `algo2.html` | 算法竞赛课程（13 讲 / 续篇） |
| `courses/python.html` | Python 入门 8 讲 |
| `courses/gongkao.html` | 行测入门 6 讲 |
| `courses/aws-educate.html` `aws-educate-catalog.html` | AWS Educate 课程全文 / 71 门课目录 |
| `exam/index.html` | 考试与题库导航 |
| `exam/guofang.html` | 国防教育刷题（单选/多选/判断，判分与错题本） |
| `exam/quiz.html` | 学堂自测（16 课 × 8 题，判分 + 解析，成绩存本机） |
| `exam/gongkao.html` | 公考专区（图形推理 354 题逐题解析） |
| `exam/calendar.html` | 全年考试日历（报名/笔试节奏 + 我的考试清单） |
| `media/wsvideos.html` | 世赛比赛视频馆（历届官方影像 + B 站直看） |
| `media/bilibili.html` | B 站精选视频库（装机 / 计算机科学 / 编译原理 / 云计算进阶，按 UP 主与时长筛选） |
| `media/pdfview.html` | 站内文档阅读器 |
| `red/index.html` | 红色经典入口 |
| `red/maoxuan.html` | 《毛泽东选集》1–5 卷全文 229 篇 + 诗词 |
| `red/socialism.html` | 社会主义实践 · 研究生研究中心 |
| `dev/index.html` | 开发者免费服务总表（整合 ripienaar/free-for-dev：57 类 1229 项，数据 `dev/ffd-data.js`） |
| `files/` | 课程与题库原始资料（730 份：ICPC / 蓝桥杯 / 图论 / 题解 …），被页面与资料中心按需引用 |
| `data/` | 学习引擎数据 |

## 改导航 / 加页面

导航片段是**复制粘贴**的：改一处不够，要批量改。加新页时：

1. 放到上表对应的子目录（别丢在 `learn/` 根）。
2. 复制同目录邻居的 `<nav>` 片段，注意相对路径（根页 `cloud/index.html`，子目录页 `../cloud/index.html`）。
3. 把 URL 加进根 `sitemap.xml`、`sw.js` 预缓存清单，检索内容加进 `searchidx.js`。
4. 目录契约详见 [../docs/STRUCTURE.md](../docs/STRUCTURE.md)。
