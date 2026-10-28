/* =====================================================================
   全真模拟卷 · 2022 广西职业院校技能大赛高职组《云计算》赛项 赛卷
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-20 全文，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文（8 大任务，按平台归组）：
   私有云50（基础运维5/搭建15/运维15/运维开发15）+ 容器云50（Docker 与私有仓库5/
   GPMall 商城容器化15/GitLab+Jenkins CI-CD15/K8s 部署运维15）。
   特点：RAID5+热备盘 / http 提升 https / GPMall 六容器商城 / 指定版本
   Jenkins+GitLab 离线部署；小题分值按结构估计。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['guangxi2022']={
 id:'guangxi2022',
 name:'2022 广西省赛真题全真卷 · 云计算赛项 赛卷',
 tag:'省赛真题卷',
 order:4.5,
 desc:'广西 2022 赛卷（★★★☆☆，8 大任务完整赛卷）：私有云 50 + 容器云 50。特色考点——RAID5+热备盘、云平台 http 提升 https、GPMall 商城六容器化、指定版本 Jenkins/GitLab 离线 CI/CD，练中间件与存储运维细节。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《2022 广西云计算赛项赛卷》全文，题库 ZT-20）；任务内小题分值为按结构估计',
 env:'双机虚拟机（controller + compute，CentOS 7 双网卡 Vlan x/y，iaas-xiandian 离线脚本）+ Docker/Harbor + 指定版本 Jenkins/GitLab 镜像 + GPMall 软件包（gpmall-single.tar）',
 rules:'<b>原文赛制</b>：① 表中 x、y 为 vlan 号（每人两个 vlan 号），z 为工位号 ② 按图表检查硬件连线及网络设备配置，确保网络连接正常 ③ 考试资源包与附件均在考位信息表中给出 ④ 自行修改服务器密码，提交时确认 IP/用户名/密码 ⑤ 每题完成后提交指定节点的用户名、密码和 IP 到答题框。',
 modules:[
 {
  name:'模块一 私有云（50 分 · 建议 120 分钟）',
  minutes:120,
  brief:'<p><b>原文背景</b>：企业使用 OpenStack 搭建云平台，实现资源池化弹性管理、企业应用集中管理、统一安全认证和授权。<b>IP 规划（原文表1）</b>：Controller eth0 192.168.x.10/24、eth1 192.168.y.10/24；Compute .20；PC-1 172.24.z.2/24（x/y 为 vlan 号、z 为工位号）。</p>',
  tasks:[
  {title:'任务1 · 基础运维任务（5 分）',
   brief:'<p>原文题目 1–5：</p>',
   checks:[
    {d:'题1 基础环境配置：主机名/hosts/关闭防火墙且开机不启动/SELinux Permissive',p:1},
    {d:'题2 镜像挂载：CentOS-7 与 chinaskill_cloud_iaas 挂到 /opt/centos、/opt/openstack',p:1},
    {d:'题3 Yum 源配置：vsftpd + ftp.repo（ftp 地址用主机名形式）',p:1},
    {d:'题4 时间同步：controller 部署 chrony 服务端，compute 指定其为上游 NTP',p:1},
    {d:'题5 计算节点利用空白分区划分 2 个 100G 分区',p:1}
   ],
   refs:['mount -o loop 两个 iso；/etc/yum.repos.d/ftp.repo','chrony：server 段 + allow；lsblk 分区'],
   sol:'五道送分题按检查单顺序做，ftp.repo 的地址必须写主机名不是 IP。'},
  {title:'任务2 · OpenStack 搭建任务（15 分）',
   brief:'<p>原文题目 1–8（iaas-xiandian 脚本链，openrc.sh 按表2 配置变量）：</p>',
   checks:[
    {d:'题1 基础安装：双节点 iaas-xiandian + /etc/xiandian/openrc.sh 表2 变量',p:2},
    {d:'题2 数据库安装：iaas-install-mysql.sh（MariaDB/Memcached/etcd）',p:2},
    {d:'题3 Keystone 服务安装',p:2},
    {d:'题4 Glance 安装',p:2},
    {d:'题5 Nova 双节点安装',p:2},
    {d:'题6 Neutron 双节点安装（默认 vlan 模式）',p:2},
    {d:'题7 Dashboard 安装',p:2},
    {d:'题8 Cinder 双节点安装',p:1}
   ],
   refs:['iaas-install-* 脚本按序执行；openrc.sh 密码 000000 一套','openstack service list 逐项验证'],
   sol:'标准 xiandian 链：八步按序，Neutron 记得是 vlan 模式；每步脚本日志留痕。'},
  {title:'任务3 · OpenStack 运维任务（15 分）',
   brief:'<p>原文题目 1–8：</p>',
   checks:[
    {d:'题1 镜像管理：基于 cirros-0.3.4 镜像创建名为 cirros 的镜像',p:1.5},
    {d:'题2 实例类型：创建 Fmin（ID 1/1024MB/10GB/1 vcpu）',p:1.5},
    {d:'题3 网络：创建 extnet/extsubnet（192.168.y.0/24，网关 192.168.y.1）',p:1.5},
    {d:'题4 云主机：cirros+Fmin+extnet 创建并启动 VM1，PC 可远程登录',p:2},
    {d:'题5 Cinder：lvm 卷类型 + 40G block 云硬盘附加到 VM1',p:2},
    {d:'题6 Raid 管理：4×5G 分区组 /dev/md5（raid5）+ 1 热备盘',p:2.5},
    {d:'题7 数据库主从：vm1 主库/vm2 从库（密码 000000）',p:2},
    {d:'题8 云平台安全策略：访问策略从 http 提升至 https',p:2}
   ],
   refs:['openstack flavor create --id 1 …；mdadm -C /dev/md5 -l 5 -n 4 -x 1','docs/tutorial/04-HTTPS与证书-保姆级.md：平台 http→https 证书链路'],
   sol:'RAID5 用最后分区作热备盘（-x 1），cat /proc/mdstat 验证；https 提升看 horizon 前端证书生效。'},
  {title:'任务4 · OpenStack 运维开发任务（15 分）',
   brief:'<p><b>原文注明：本任务只公布考试范围，不公布赛题。</b>此任务包含 2–4 个子任务，内容涉及编写 Python 脚本调用 OpenStack API 对云平台进行管理和运维；使用自动化运维工具 ansible 对云主机进行批量系统配置、批量程序部署、批量运行命令等运维操作。</p>',
   checks:[
    {d:'Python 脚本调用 OpenStack API 管理运维云平台（2–4 个子任务，范围题）',p:8},
    {d:'Ansible 批量系统配置/批量程序部署/批量运行命令',p:7}
   ],
   refs:['keystone token + REST API 或 openstacksdk；查询/管理虚拟机脚本','docs/tutorial/13-自动化运维-保姆级.md：ansible 批量操作三件套'],
   sol:'范围题自查证据链：每个子任务「做了什么 + 怎么验证」各留一屏。'}
  ]
 },
 {
  name:'模块二 容器云（50 分 · 建议 120 分钟）',
  minutes:120,
  brief:'<p><b>原文背景</b>：Docker CE + 私有仓库 + 微服务商城全容器化部署；GitLab + Jenkins 构建 CI/CD 实现 DevOps 流程；Kubernetes 容器云平台部署与运维。<b>原文架构（图2/表2）</b>：gpmall.sql（MySQL）+ dist（Nginx 前端）+ gpmall-shopping（8081）+ gpmall-user（8082）+ user-provider/shopping-provider 后端。</p>',
  tasks:[
  {title:'任务5 · Docker CE 及私有仓库安装任务（5 分）',
   brief:'<p>原文题目 1–4：</p>',
   checks:[
    {d:'题1 master、node 各节点安装 DockerCE 和 docker-compose',p:1.5},
    {d:'题2 master 安装私有仓库，导入 /opt/images 全部镜像并推送',p:1.5},
    {d:'题3 wordpress 编排：wordpress:latest 82:80 + mysql:5.6（root 密码 123456、建库 wordpress）',p:1.5},
    {d:'题4 容器基础操作：停止并删除 wordpress 容器',p:0.5}
   ],
   refs:['docker load → tag → login → push','docker-compose up -d；mysql 库初始化验证'],
   sol:'推送后到仓库页面验证；wordpress 题四条要求一个不落。'},
  {title:'任务6 · 基于 Docker 容器的 web 应用系统部署（15 分）',
   brief:'<p>原文题目 1–6（基于 gpmall-single.tar 构建 chinaskill-*:v1.1 系列镜像，基础镜像 centos:centos7.5.1804、作者 Chinaskill）：</p>',
   checks:[
    {d:'题1 容器化 Redis：chinaskill-redis:v1.1（bind 0.0.0.0/免密关保护模式/6379/自启）',p:2.5},
    {d:'题2 容器化 MariaDB：chinaskill-mariadb:v1.1（密码 123456/建库 gpmall 导入 gpmall.sql/UTF-8/3306）',p:2.5},
    {d:'题3 容器化 Zookeeper：chinaskill-zookeeper:v1.1（2181，运行容器 myzookeeper）',p:2.5},
    {d:'题4 容器化 Kafka：chinaskill-kafka:v1.1（9092）',p:2.5},
    {d:'题5 容器化 Nginx：反向代理 80 → 8081/8082/8083 + dist 前端（80/443/8081/8082/8083）',p:2.5},
    {d:'题6 编排部署 GPMall：mysql/redis/kafka/zookeeper/nginx 五容器 docker-compose',p:2.5}
   ],
   refs:['六个 Dockerfile + /root/chinaskillmall/docker-compose.yaml','商城首页 curl 验证：nginx 反代四条 upstream'],
   sol:'六题各 2.5 分按镜像逐个构建；最后 compose 一次拉起五容器并打开商城首页留证。'},
  {title:'任务7 · 基于 Kubernetes 构建持续集成（15 分）',
   brief:'<p>原文背景：采用 GitLab + Jenkins 构建 CICD 环境，实现可视化容器生命周期管理、应用发布和版本迭代更新。原文题目 1–5：</p>',
   checks:[
    {d:'题1 Jenkins：镜像 jenkins/jenkins:2.262-centos（8080:80/root 运行/离线插件/chinaskill·000000/任何用户可做任何事）',p:3},
    {d:'题2 GitLab：镜像 gitlab-ce:12.9.2-ce.0（1022:22/81:80/443:443/always/root·00000000/新建 ChinaskillProject 并上传代码）',p:3},
    {d:'题3 Jenkins 连接 GitLab：Outbound requests/Access Tokens/取消 /project 验证/连通性测试',p:3},
    {d:'题4 Jenkins 连接 maven：docker in docker 方式安装 maven 并配置',p:3},
    {d:'题5 配置 CI/CD：流水线 ChinaskillProject/流水线脚本/Webhook/Harbor 公开项目 chinaskillproject',p:3}
   ],
   refs:['docker run jenkins/gitlab 指定端口与重启策略；离线插件目录','GitLab Access Tokens → Jenkins 凭据；Harbor 建项目'],
   sol:'指定版本镜像按题面参数逐项核对；连通性测试成功截图是题3 的采分点。'},
  {title:'任务8 · Kubernetes 容器云平台部署与运维（15 分）',
   brief:'<p><b>原文注明：本任务只公布考试范围，不公布赛题。</b>本任务内容为：Kubernetes 集群环境搭建和运维、基于 Kubernetes 集群的应用系统部署与运维。</p>',
   checks:[
    {d:'Kubernetes 集群环境搭建和运维（范围题：节点 Ready/组件健康/运维操作留痕）',p:7},
    {d:'基于 Kubernetes 集群的应用系统部署与运维（范围题：应用可访问/运维记录）',p:8}
   ],
   refs:['kubeadm init + CNI；kubectl get nodes/cs/pods -A','应用部署 manifest + Service 暴露验证'],
   sol:'范围题按检查单自证：集群健康一张图 + 应用部署一条链 + 运维操作一组记录。'}
  ]
 }
 ]
};
})();
