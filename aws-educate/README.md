# AWS 离线学习包

> **AWS Educate 的全部可用学习资源，本地离线化。**

AWS Educate 71 门官方课程 + 7 条官方学习路径（2026-10 登录态实测抓取），
每门课逐门映射到站内可离线阅读的材料。**断网也能学 AWS。**

---

## 先打开这个

| 你想做的事 | 打开 |
|---|---|
| **浏览**（推荐入口） | **`aws-educate/index.html`** —— 单文件、数据内联、双击即用，断网也能搜索筛选 |
| 看课程映射的**原始数据**（给工具读） | `catalog.json` · `learning-paths.json` |
| 读**方法与边界** | [`offline.md`](offline.md) |
| 读**唯一有全文的官方课** | [`course.zh.md`](course.zh.md) |

---

## 7 条官方学习路径（登录态实测，2026-10-15）

| 路径 | 课数 | 官方描述 | 对你的价值 |
|---|---|---|---|
| **Getting Started** | 5 | New to cloud computing? Start here. | ★★★ **零基础从这里进**。5 门就是整个平台的入口 |
| **Core Concepts** | 6 | Dive deeper into specific fundamental cloud skills. | ★★ 过完 Getting Started 再进 |
| **Cloud Challenges** | 15 | Learn basic cloud concepts in short form scenarios. | ★★★ **15 门全是 0.5–2h 的「Explore XX」短课，是 71 门的主体**。碎片时间刷 |
| **Twitch Series on-demand** | 3 | Dive into learning with AWS expert instructors | ★★ 1 小时一集边看边做，性价比最高的入门形式 |
| **Professional Skills** | 4 | Enhance your career trajectory | ★ 「问题解决流程」与排错方法论同源 |
| **Exploring Cloud's Real-World Impact** | 3 | Learn how cloud can fix problems | ★★ Sustainability 占 WSOS 权重 10% |
| **Artificial Intelligence and ML** | 5 | Learn AI and machine learning skills | ★ 与赛项弱相关，零基础可跳过 |

> **「路径」和「分类」是两回事。** catalog.json 里的 7 个分类（Cloud Computing / Security /
> Analytics…）是**主题标签**；而这里的 7 条路径是**AWS 官方推荐的刷课顺序**，
> 两者交叉覆盖同一批课程。**跟着路径刷，不要按分类挑。**

### 门户的筛选维度

`Course Features` · `Skills` · `Language` · `Level` · `Duration`

> 注意：`Skills` 这个维度是**门户里有、catalog.json 里没有**的一层信息。
> 说明 AWS 内部按技能域组织课程，比 7 个主题分类更细。

### 2026-10 门户公告（会影响你的学习计划）

| 公告 | 对你的影响 |
|---|---|
| **4 门职业技能课新增 AI 模块**（沟通/问题解决/目标设定/简历撰写） | ⚠️ 内容已变，之前做的笔记需要重看 |
| **徽章与 Emerging Talent Community 绑定** | ⚠️ 同属 2026 退役范围，入口价值在下降 |
| 出现新认证 **AWS Certified AI Practitioner** | 若走 AI 方向可关注 |
| **AWS Skills Centers** 免费直播培训（线上/线下） | 想真人带学可关注 |

### 抓取边界（说明白，别误会）

| 拿到了 | 没拿到 |
|---|---|
| 7 条学习路径 + 描述 + 课数 | 完整 71 门的门户内清单（在 Aura 后台，DOM 抓不到） |
| 16 次课程提及的级别/时长/分类 | 课程正文（版权属 Amazon，且托管在 Canvas 后） |
| 5 个筛选维度名 | 各筛选维度的完整可选项 |
| 课程进度、公告 | |

**已核对**：门户首页只渲染 7 条路径、每条 2–3 门精选课；71 门的完整元数据以 `catalog.json` 为准。

---

## 三套刷课路线（选一条，别混）

### 路线 A · 零基础速通（半天到一天）

= 官方「Getting Started」路径的 5 门课，顺序别改。

### 路线 B · 4 周备赛

以官方 **Cloud Challenges（15 门「Explore XX」短课）** 为主体 —— 每门 0.5–2 小时。

### 路线 C · 长期

AWS Educate 只到入门级，**撑不起长期**。正确用法：
- **W1–W2**：用 71 门课建概念地图（99.5 学时够用）
- **W2 之后**：切到本站 `docs/deep/` 深度教材
- **W6 之后**：按 `docs/mastery/05-全平台地图.md` 的对照表横向对比 AWS/Azure/GCP/华为云

---

## 与本站内容的分工

| AWS Educate | 本站 | 说明 |
|---|---|---|
| 课程正文（需登录） | `docs/tutorial/`（保姆级） | 教程更细、含「应该看到什么」「出错了怎么办」 |
| 71 门课的官方实验 | `docs/cloudlab/` L1–L4 | 真虚拟机 + 自动评分 |
| AWS 服务概念 | `docs/knowledge/05-公有云核心-AWS.md` | 提纲索引 |
| AWS 深度 | `docs/deep/` | 专家级，有代码有验收 |

> **两边大量重叠，重复学是最大的浪费。** 按分工表选一边学。

---

## 维护

本目录由 `tools/verify_all.py` 的站内链接检查把关。
AWS 离线包页面数据内联，双击 `index.html` 即可离线使用。