/* =====================================================================
   全真模拟卷 · 2023-2024 江西省职业院校技能大赛（高职组）云计算应用 赛卷 1
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-06 全文，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文：
   私有云30（搭建5/运维15/开发10）+ 容器云30（搭建5/运维15/开发10）+
   公有云40（搭建5/运维10/开发10，边缘部分原文摘录未逐题收录）。
   特点：国赛同源卷（Manila/SkyWalking/JumpServer/Redis 一主二从三哨兵/
   Ansible Kafka/gpmall 一键脚本/自定义调度器 Restful/RocketChat 上云）。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['jiangxi']={
 id:'jiangxi',
 name:'2023-2024 江西省赛真题卷 · 云计算应用 赛卷 1',
 tag:'省赛线 · 真题原文',
 order:5,
 desc:'江西 2023-2024 省赛赛卷 1（★★★★☆，国赛同源三模块）：私有云 30 + 容器云 30 + 公有云 40。Manila 共享存储 + SkyWalking + JumpServer 堡垒机 + Redis 一主二从三哨兵；容器云监控四件套 + Jenkins/GitLab + Ingress Gateway；公有云 RocketChat 上云 + mariadb chart NodePort。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《江西赛卷 1》全文，题库 ZT-06）；小题分值为按结构估计；模块三边缘计算部分原文摘录未逐题收录，按原文背景（云边端一体化）补全练习',
 env:'双机虚拟机（controller + compute，CentOS 7.9/openEuler，OpenStack Train 离线包）+ K8s 双节点（master + node）+ 任一国内公有云账号',
 rules:'<b>原文赛制</b>：① 集群模式，每队独立租户，2 名选手账号密码相同 ② x 为赛位号，第二块网卡地址自行创建 ③ 账号资源/竞赛资源包/附件在考位信息表与设备确认单中给出 ④ 自行修改服务器密码 ⑤ 调优/排错题只公布范围不公布赛题。',
 modules:[
 {
  name:'模块一 私有云（30 分 · 建议 80 分钟）',
  minutes:80,
  brief:'<p><b>原文背景</b>：OpenStack 私有云 + Kubernetes 云原生 + 国内公有云边缘计算。<b>IP 规划（原文表1）</b>：controller/compute eth0 172.129.x.0/24（x=赛位号），eth1 自定义。<b>本卷搭建 13 小题为省赛最多</b>（含无秘 ssh 与 Manila）。</p>',
  tasks:[
  {title:'任务1 · 私有云服务搭建（5 分 · 13 小题）',
   brief:'<p>原文 1.1.1–1.1.13：</p>',
   checks:[
    {d:'1.1.1 基础环境：controller/compute 主机名 + hosts 映射',p:0.4},
    {d:'1.1.2 yum 源：http 服务地址配 http.repo（双节点）',p:0.4},
    {d:'<b>1.1.3 配置无秘钥 ssh（controller 免密访问 compute）</b>',p:0.4},
    {d:'1.1.4 双节点安装 openstack-iaas 软件包',p:0.4},
    {d:'1.1.5 MariaDB/RabbitMQ 安装与调优',p:0.4},
    {d:'1.1.6 Keystone 安装并创建用户',p:0.4},
    {d:'1.1.7 Glance 安装：上传镜像并设置启动参数',p:0.4},
    {d:'1.1.8 Nova 安装与相关配置',p:0.4},
    {d:'1.1.9 Neutron 安装',p:0.4},
    {d:'1.1.10 Dashboard 安装 + Django 数据改为文件存储',p:0.4},
    {d:'1.1.11 Swift 安装 + cirros 镜像分片存储',p:0.4},
    {d:'1.1.12 Cinder 安装 + 计算节点块存储扩容',p:0.4},
    {d:'<b>1.1.13 Manila 服务安装与使用（共享文件存储）</b>',p:0.2}
   ],
   refs:['ssh-keygen -t rsa && ssh-copy-id compute','iaas 脚本链尾追加 manila-install.sh','openstack service list 验证 13 项'],
   sol:'13 小题平均每题不到 6 分钟——先全跑完 iaas 主链，再回头补 ssh/Manila 两个小项。'},
  {title:'任务2 · 私有云服务运维（15 分）',
   brief:'<p>原文 1.2.1–1.2.10（<b>Redis 三哨兵 + JumpServer 是本卷特色</b>）：</p>',
   checks:[
    {d:'1.2.1 Glance 开放镜像权限：glance-cirros 共享给 demo 项目',p:1.5},
    {d:'1.2.2 SkyWalking 应用部署：ES + SkyWalking + gpmall 主机接入监控',p:2},
    {d:'1.2.3 Glance 镜像压缩：CentOS7.5-compress.qcow2',p:1.5},
    {d:'1.2.4 Glance 对接 Cinder 存储（后端切换）',p:1.5},
    {d:'1.2.5 Heat 模板创建容器：/root 下 yaml 创建 heat-swift 容器',p:1.5},
    {d:'1.2.6 Nova 清除缓存：长时间不用的镜像缓存自动删除',p:1.5},
    {d:'<b>1.2.7 Redis 集群：一主二从三哨兵架构部署</b>',p:2},
    {d:'<b>1.2.8 Redis AOF 调优：避免 AOF 文件过大自动重写</b>',p:1.5},
    {d:'<b>1.2.9 JumpServer 堡垒机部署并对接控制/计算节点</b>',p:1.5},
    {d:'1.2.10 平台调优或排错（范围题：按检查单自证）',p:0.5}
   ],
   refs:['openstack image add-project glance-cirros --project demo','sentinel monitor mymaster <ip> 6379 2','auto-aof-rewrite-min-size / auto-aof-rewrite-percentage','JumpServer：allinone 安装 → 资产管理接入 controller/compute'],
   sol:'Redis 一主二从三哨兵 = replicaof×2 + sentinel.conf×3，哨兵 quorum=2；JumpServer 装完还要「对接」才算分。'},
  {title:'任务3 · 私有云运维开发（10 分）',
   brief:'<p>原文 1.3.1–1.3.4（<b>Ansible 双题 + gpmall 一键脚本</b>）：</p>',
   checks:[
    {d:'<b>1.3.1 Shell 一键部署脚本：gpmall 商城应用系统</b>',p:3},
    {d:'1.3.2 Ansible 部署 FTP 服务',p:2.5},
    {d:'<b>1.3.3 Ansible Playbook 部署 ZooKeeper + Kafka</b>',p:3},
    {d:'1.3.4 OpenStack 自动化运维工具（范围题）',p:1.5}
   ],
   refs:['gpmall：包安装顺序 kafka→zookeeper? 不——gpmall 链路 redis/mariadb/zookeeper→kafka→jar 包','vsftpd role：install/template/conf/service','Kafka 依赖 ZooKeeper，playbook 内加等待就绪'],
   sol:'一键脚本 = 顺序 + 判活；Ansible 双题考 role 拆分与变量抽取。'}
  ]
 },
 {
  name:'模块二 容器云（30 分 · 建议 70 分钟）',
  minutes:70,
  brief:'<p><b>原文背景</b>：Kubernetes + KubeVirt 全运行时管理 + K8s CI/CD + Istio 灰度发布。与国赛容器云模块同源：<b>监控四件套 + Jenkins/GitLab 双装</b>。</p>',
  tasks:[
  {title:'任务1 · 容器云服务搭建（5 分）',
   brief:'<p>原文 2.1.1：</p>',
   checks:[
    {d:'用 OpenStack 创建两台云主机作 master/node，K8s 集群部署完成',p:2},
    {d:'Istio 服务网格部署',p:1},
    {d:'KubeVirt 虚拟化部署',p:1},
    {d:'Harbor 镜像仓库部署',p:1}
   ],
   refs:['kubeadm init --image-repository … --pod-network-cidr …','istioctl install；kubectl apply -f kubevirt-operator.yaml'],
   sol:'K8s → Istio → KubeVirt → Harbor 四连装，与广西/国赛同构。'},
  {title:'任务2 · 容器云服务运维（15 分）',
   brief:'<p>原文 2.2.1–2.2.12（<b>监控四件套 + Jenkins/GitLab</b>）：</p>',
   checks:[
    {d:'2.2.1 Dockerfile 构建 exporter 镜像（centos 装 Node-Exporter + 自启）',p:1},
    {d:'2.2.2 Dockerfile 构建 alert 镜像（centos:latest 装 Alertmanager）',p:1},
    {d:'2.2.3 Dockerfile 构建 grafana 镜像（centos 装 Grafana）',p:1},
    {d:'2.2.4 Dockerfile 构建 prometheus 镜像（centos 装 Prometheus）',p:1},
    {d:'2.2.5 docker-compose.yaml 编排部署监控系统（exporter/alert/grafana/prometheus）',p:2},
    {d:'2.2.6 Jenkins 部署到 default 命名空间：离线插件 + 登录信息 + 授权策略',p:1},
    {d:'2.2.7 GitLab 部署到 default 命名空间：root 密码 + 公开项目 + 代码上传',p:1},
    {d:'2.2.8 Jenkins 新建流水线连接 GitLab + WebHook 配置',p:1.5},
    {d:'2.2.9 CI/CD：代码编译→镜像构建推送→自动发布 K8s',p:2},
    {d:'2.2.10 Istio Ingress Gateway：Bookinfo 部署 + 创建网关外部可访问',p:1.5},
    {d:'2.2.11 KubeVirt 创建 VM（名称 exam，指定内存/CPU/网卡/磁盘）',p:1.5},
    {d:'2.2.12 容器云平台调优或排错（范围题）',p:0.5}
   ],
   refs:['kube-prometheus 或自建 compose 数据贯通','Jenkins-GitLab：凭据 + webhook 触发','Gateway + VirtualService 对外暴露 productpage'],
   sol:'监控四件套用同一 Dockerfile 模板；Bookinfo 先 default 部署再建网关，两步分开算分。'},
  {title:'任务3 · 容器云运维开发（10 分）',
   brief:'<p>原文 2.3.1–2.3.3（<b>SDK 与 Restful 双方式</b>）：</p>',
   checks:[
    {d:'<b>2.3.1 K8s Python：SDK 方式管理 job 服务</b>',p:3.5},
    {d:'<b>2.3.2 K8s Python：Restful API 方式管理自定义调度器</b>',p:3.5},
    {d:'2.3.3 K8s 自动化运维工具（范围题）',p:3}
   ],
   refs:['BatchV1Api 管理 Job；requests 直打 apiserver /apis/scheduling.k8s.io','schedulerName + 第二调度器 Deployment'],
   sol:'SDK 题 import kubernetes；Restful 题用 token + requests——两种客户端别写混。'}
  ]
 },
 {
  name:'模块三 公有云（40 分 · 建议 90 分钟）',
  minutes:90,
  brief:'<p><b>原文背景</b>：国内公有云 + 云原生 DevOps + 云边端一体化边缘计算。<b>本卷特色：Node.js 环境 + RocketChat 上云 + mariadb chart 双题</b>。<b>注</b>：边缘计算部分原文摘录未逐题收录，以下按原文背景补全练习。</p>',
  tasks:[
  {title:'任务1 · 公有云服务搭建（5 分 · 11 小题）',
   brief:'<p>原文 3.1.1–3.1.11：</p>',
   checks:[
    {d:'3.1.1 私有网络管理（VPC 创建）',p:0.4},
    {d:'3.1.2 云实例管理（创建两台）',p:0.4},
    {d:'3.1.3 数据库：intnetX-mysql 网络两台 chinaskill-sql 云主机装 MongoDB',p:0.4},
    {d:'3.1.4 MongoDB 主从数据库配置',p:0.4},
    {d:'<b>3.1.5 Node.js 环境管理：用提供的压缩包安装</b>',p:0.4},
    {d:'3.1.6 安全组创建',p:0.4},
    {d:'<b>3.1.7 RocketChat 上云：用 http 服务器提供文件部署</b>',p:0.6},
    {d:'3.1.8 公网 NAT 网关创建',p:0.4},
    {d:'3.1.9 云服务器备份：存储库 server_backup（100G）+ 镜像 chinaskill-image',p:0.6},
    {d:'3.1.10 负载均衡器 chinaskill-elb 创建',p:0.5},
    {d:'3.1.11 弹性伸缩启动配置创建',p:0.5}
   ],
   refs:['node：解压 + PATH 环境变量','RocketChat：mongodb 依赖 + snap/tar 部署两路','备份存储库容量 100G 别填错'],
   sol:'11 小题全是控制台/命令行小步操作，控制在 25 分钟内。'},
  {title:'任务2 · 公有云服务运维（10 分）',
   brief:'<p>原文 3.2.1–3.2.6（<b>mariadb chart 双题是本卷特色</b>）：</p>',
   checks:[
    {d:'3.2.1 云容器引擎：创建 x86 架构容器云集群',p:2},
    {d:'3.2.2 插件管理安装 Dashboard 可视化监控',p:1.5},
    {d:'3.2.3 安装 kubectl 并操作 kcloud 集群',p:1.5},
    {d:'3.2.4 安装 Helm 包管理器',p:1.5},
    {d:'<b>3.2.5 用 mariadb-7.3.14.tgz chart 部署 mariadb 服务</b>',p:1.75},
    {d:'<b>3.2.6 修改 chart 配置：mariadb 改 NodePort 模式访问</b>',p:1.75}
   ],
   refs:['helm install mariadb mariadb-7.3.14.tgz','values.yaml：service.type=NodePort 或 helm upgrade --set service.type=NodePort'],
   sol:'双题连做：先 install 再 upgrade 改 NodePort——同一 release 别重装。'},
  {title:'任务3 · 公有云运维开发（10 分）',
   brief:'<p>原文 3.3.1–3.3.5（<b>API + SDK 双通道安全组</b>）：</p>',
   checks:[
    {d:'3.3.1 开发环境搭建：云主机装 Python3.68 运行环境与 SDK 依赖库',p:2},
    {d:'3.3.2 安全组管理：调用 API 接口增删查改',p:2},
    {d:'3.3.3 安全组规则管理：调用 SDK 增删查改',p:2},
    {d:'3.3.4 云主机管理：调用 SDK 增删查改',p:2},
    {d:'3.3.5 公有云自动化运维程序开发（范围题）',p:2}
   ],
   refs:['pip install 官方 SDK；requests + token 直打 API','安全组与安全组规则是两层资源，接口路径不同'],
   sol:'API 题与 SDK 题各写各的；环境版本号 3.68 原文如此（3.6.8）。'},
  {title:'任务4 · 边缘计算系统运维（10 分 · 背景补全）',
   brief:'<p><b>补全说明</b>：原文摘录未含本节逐题，按背景「云边端一体化」补全：</p>',
   checks:[
    {d:'云端部署：KubeEdge CloudCore 就绪并启动',p:3},
    {d:'边端部署：EdgeCore 接入并启动',p:4},
    {d:'边缘应用部署与调试',p:3}
   ],
   refs:['keadm init --advertise-address=<云端IP>','keadm join --cloudcore-ipport=<IP>:10000 --token=…'],
   sol:'KubeEdge 三段式与国赛/贵州卷一致，练熟一套通吃。'},
  {title:'任务5 · 边缘计算云应用开发（5 分 · 背景补全）',
   brief:'<p><b>补全说明</b>：同上，按背景补全：</p>',
   checks:[
    {d:'云应用微服务开发（范围题：边端采数 → 云端可见闭环）',p:5}
   ],
   refs:['MQTT broker + 云端 rule'],
   sol:'范围题按「能演示的最小闭环」自证。'}
  ]
 }
 ]
};
})();
