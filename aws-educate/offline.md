# AWS 离线学习包 · 离线使用说明

> **AWS Educate 的全部可用学习资源，本地离线化。**
> 课程正文需登录且版权属 Amazon，无法下载。
> 本包只给**元数据与结构** + **站内替代材料的映射**。

## 为什么课程正文下不来

<|constrain|> 项目 | 状态 |
|---|---|
| AWS Educate 学生门户 `/student/s/content` | 需登录 |
| AWS Educate 课程 `/student/s/courses` | 需登录 |
| AWS Educate 课程详情 `/student/s/content/982` | 需登录 |
| AWS Educate API `/api/student/content` | 需登录 |
| `aws.amazon.com` / `skillbuilder.aws` | webfetch 不可达（transport error），但浏览器可打开 |

**结论**：AWS Educate 课程正文**无法离线化**。本包只给元数据与结构。

## 断网 5 步

1. **先注册** AWS Educate（按 `亚马逊云科技Educate 自学平台注册使用向导(1).pdf`）
2. **打开** `aws-educate/index.html`（单文件、数据内联、双击即用）
3. **跟着 7 条官方学习路径刷**（零基础从「入门起步」开始）
4. **每门课展开后**，看「AWS 服务映射」，去站内对应教程学
5. **有脚本的课**，学完跑一遍 `tools/verify_all.py` 验证

## 7 条官方学习路径

| 路径 | 课数 | 对零基础的价值 |
|---|---|---|
| **Getting Started** | 5 | ★★★ 零基础从这里进 |
| **Core Concepts** | 6 | ★★ 过完 Getting Started 再进 |
| **Cloud Challenges** | 15 | ★★★ 15 门全是 0.5–2h 的短课，碎片时间刷 |
| **Twitch Series on-demand** | 3 | ★★ 1 小时一集边看边做 |
| **Professional Skills** | 4 | ★ 「问题解决流程」与排错方法论同源 |
| **Exploring Cloud's Real-World Impact** | 3 | ★★ Sustainability 占 WSOS 10% |
| **AI and Machine Learning** | 5 | ★ 与赛项弱相关，零基础可跳过 |

## 三套刷课路线

详见 `aws-educate/README.md` §4。

## 与本站内容的分工

| AWS Educate | 本站 | 说明 |
|---|---|---|
| 课程正文（需登录） | `docs/tutorial/`（保姆级） | 教程更细、含「应该看到什么」「出错了怎么办」 |
| 71 门课的官方实验 | `docs/cloudlab/` L1–L4 | 真虚拟机 + 自动评分 |
| AWS 服务概念 | `docs/knowledge/05-公有云核心-AWS.md` | 提纲索引 |
| AWS 深度 | `docs/deep/` | 专家级，有代码有验收 |

> **两边大量重叠，重复学是最大的浪费。** 按分工表选一边学。

## 维护

本目录由 `tools/verify_all.py` 的站内链接检查把关。
AWS 离线包页面数据内联，双击 `index.html` 即可离线使用。