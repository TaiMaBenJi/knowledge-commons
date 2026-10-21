# L1 · Linux 基础 · 任务书（满分 100）

> 环境：你的练习虚拟机（Rocky 9 / Ubuntu 24.04），root 或 sudo 权限
> 建议限时：90 分钟 · 及格 60 · 优秀 85
> 规则与世赛一致：**按评分点交付，做对得分，做错不得分**；做完运行评分脚本验收
> 评分：`sudo bash grade_l1.sh`（评分点逻辑与本题面一一对应）

## 背景

你入职云运维部第一天，主管给你一台全新虚拟机，要求按公司规范完成初始化并跑起第一个业务。

## 任务清单（16 个评分点）

| # | 分值 | 评分点 | 提示（卡住再看） |
|---|-----|--------|------------------|
| 1 | 5 | 主机名为 `cloudlab` | `hostnamectl set-hostname cloudlab`（重连生效） |
| 2 | 5 | 时区 `Asia/Shanghai` | `timedatectl set-timezone Asia/Shanghai` |
| 3 | 5 | 用户 `deployer` 已创建 | `useradd -m deployer` |
| 4 | 5 | `deployer` 有 sudo 权限 | `usermod -aG wheel deployer`（Ubuntu 用 `sudo` 组） |
| 5 | 5 | `deployer` 已配 SSH 密钥且权限 600 | `~deployer/.ssh/authorized_keys`，属主 deployer，`chmod 600` |
| 6 | 5 | sshd 运行且监听 22 | `systemctl status sshd` · `ss -ltn \| grep 22` |
| 7 | 5 | 防火墙放行 http | firewalld：`firewall-cmd --permanent --add-service=http && firewall-cmd --reload`；ufw：`ufw allow 80/tcp` |
| 8 | 10 | nginx 运行中 | 安装 + `systemctl enable --now nginx` |
| 9 | 10 | 本机 80 返回 200 | `curl -I http://127.0.0.1/` |
| 10 | 5 | 首页含 `CloudLab` 字样 | 改 `/var/www/html/index.html`，写一句含 CloudLab 的话 |
| 11 | 10 | 自定义 systemd 服务 `app` 运行中 | 写 `/opt/cloudlab/bin/app.sh`（循环写日志即可），做 `app.service`，`daemon-reload` 后启动 |
| 12 | 5 | `/opt/backup.sh` 存在可执行 | tar 打包 `/etc` 到 `/var/backups/backup-$(date +%Y%m%d).tar.gz` |
| 13 | 5 | `/var/backups/` 有今天的 tar.gz | 手动跑一次 `/opt/backup.sh` 验证产物 |
| 14 | 10 | root 计划任务每天 2 点备份 | `crontab -e -u root`：`0 2 * * * /opt/backup.sh` |
| 15 | 10 | 磁盘挂载点 `/data` 生效 | 加一块 1G 虚拟磁盘 → `fdisk`/`parted` → `mkfs.xfs` → `mount` → 写入 `/etc/fstab` |
| 16 | 5 | `/opt/sysinfo.sh` 输出含内核版本 | `uname -r` + `free -h`，`chmod +x` |

## 验收

```bash
sudo bash grade_l1.sh        # 逐项 PASS/FAIL + 总分
sudo bash grade_l1.sh -v     # 复盘模式：显示每项的检查逻辑
```

## 世赛提示

- 每完成一项**立刻按验收方式自验**——这正是评分表思维
- 卡住先看状态：`systemctl status` → `journalctl -xe` → 日志
- 全部 PASS 后：**拍快照**，然后跑 `docs/cloudlab/fault/make_fault_l1.sh` 进入排错训练
