# 云计算世赛实战训练包 · 总说明书

> 一句话：**在你自己的 Linux 虚拟机上，按世赛评分逻辑练真功夫**——每关一张任务书（题面）+ 一个自动评分脚本（做对得分、做错不得分），像真实赛场一样验收。
> 全部免费、全部离线可复用、全部对标库里 20 章保姆级教程。

---

## 一 · 先把练习机搞起来（三选一）

| 方案 | 适合 | 最低配置 | 说明 |
|------|------|---------|------|
| **A · VMware Workstation Pro**（首选） | Windows/Linux 实体机 | 2C4G，L4 建议 4C8G | Broadcom 收购后个人使用**完全免费**（support.broadcom.com 注册下载）；新建虚拟机 → 装 Rocky 9 或 Ubuntu 24.04 |
| **B · VirtualBox** | 想全免费开源 | 同上 | virtualbox.org 下载；配 Guest Additions 更顺手 |
| **C · 云主机免费额度** | 没有合适实体机 | 1C2G 起步 | 华为云 KooLabs / 阿里云试用 / AWS 免费套餐（见资源总库 g=0「实验平台与靶场」）；注意额度与时长限制 |

**系统选择**：新手推荐 **Ubuntu 24.04 LTS**（资料多、apt 顺）；想贴赛场选 **Rocky 9**（世赛与国产化环境主流系）。两套评分脚本都兼容。

**装完必做三件事**：
1. 快照！命名 `L0-干净系统`——以后每关完成都打一个快照（世赛纪律：变更前先快照）
2. `sudo apt update && sudo apt upgrade -y`（或 `dnf update -y`）
3. 记下 IP（`ip a`），配好 SSH 终端（Windows 用 Windows Terminal / Tabby，更贴近赛场）

## 二 · 怎么用这套训练包

每关三步，**跟世赛流程一模一样**：

```bash
# ① 拿题面：浏览器打开对应 tasks/LX-xxx.md（或下载到虚拟机）——先做题，别看评分脚本
# ② 按题面交付（在虚拟机里操作）
# ③ 验收打分（在虚拟机里跑）：
curl -fsSL https://taimabenji.github.io/knowledge-commons/docs/cloudlab/grade/grade_l1.sh -o grade_l1.sh
sudo bash grade_l1.sh          # 逐项 PASS/FAIL + 总分 + 评级
sudo bash grade_l1.sh -v       # 复盘模式：显示每项检查逻辑（对完分再看，像对答案）
```

> 世赛玩法：评分前**不要**看 grade 脚本的检查逻辑——先自己交付，再用 `-v` 复盘，差距就是你要补的课。改对即得分，随时重跑。

## 三 · 关卡地图（按顺序打）

| 关卡 | 主题 | 评分脚本 | 任务书 | 对应教程 | 满分 |
|------|------|---------|--------|---------|------|
| L1 | Linux 基础（初始化/服务/备份/磁盘/计划任务） | grade_l1.sh | tasks/L1-Linux.md | 第 1/3/9 章 | 100 |
| L2 | 网络服务（DNS/HTTPS/负载均衡/健康检查） | grade_l2.sh | tasks/L2-网络服务.md | 第 2/4/5/6 章 | 100 |
| L3 | 容器化（镜像/容器/卷/Compose/私有仓库） | grade_l3.sh | tasks/L3-Docker.md | 第 10 章 | 100 |
| L4 | Kubernetes（集群/工作负载/暴露/存储/配置/弹性） | grade_l4.sh | tasks/L4-Kubernetes.md | 第 11 章 | 100 |

**评级线**：60 及格 → 85 优秀 → 拍快照进下一关。**卡关时**：先 `-v` 复盘，再回对应教程章节找答案，最后才搜索引擎。

## 四 · 故障注入排错（世赛半条命在这里）

赛程四天里排障约占四分之三（官方 TD53）。L1 打到优秀后：

```bash
curl -fsSL https://taimabenji.github.io/knowledge-commons/docs/cloudlab/fault/make_fault_l1.sh -o make_fault_l1.sh
sudo bash make_fault_l1.sh     # 确认 YES 后注入 6 个真实故障
sudo bash grade_l1.sh          # 分数掉了——限时 30 分钟排障
sudo bash grade_l1.sh          # 修回 100 = 毕业标准
```

口诀（第 7 章）：**链路 → 系统 → 服务 → 应用** 逐层定位；先 `systemctl status`，再 `journalctl -xe`。把每次故障和修法记进你的命令笔记本。

## 五 · 常见问题

- **curl 下载脚本很慢/失败？** 用浏览器直接打开脚本链接，另存为 .sh 传进虚拟机（scp / 共享文件夹均可）
- **评分脚本误报？** 脚本优先适配 Rocky 9 与 Ubuntu 24.04；其他发行版个别项（如防火墙）可能需要手工对照题面确认。发现误报欢迎提 Issue
- **L4 内存不够？** minikube `--memory=3072` 起步；或用 Killercoda / Play with Kubernetes 免费在线集群先把题面做一遍（环境不同，L4 部分评分项需自建集群才能验收）
- **打完四关然后呢？** 回 [云计算 · 世赛备战中心](../../learn/cloud/index.html) 进入「阶段五 · 竞赛级打磨」：真题轮刷（里昂 2024 评分点全录 → 韩国题面+评分标准 → 中国真题）+ 第 16 章黄金四步训练法

## 六 · 边界说明

本训练包为自学练习用途，任务与评分点为独立设计（对标世赛「评分点制」逻辑），非官方赛题；官方标准以世界技能组织当届文件为准。
