/* =====================================================================
   全真模拟卷 · 2024 广西职业院校技能大赛高职组 云计算应用赛项 样卷
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-16 六套合集之样卷，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文：
   私有云30（搭建5/运维15/开发10）+ 容器云30（搭建5/运维15/开发10）+
   公有云40（搭建5/运维10/开发10/边缘运维10/边缘开发5）。
   特点：RAID5+热备盘、RabbitMQ 三级连接数、Redis 主从 + Ceph、
   Explorer 四镜像 compose 编排、ChartMuseum + WordPress chart。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['guangxi']={
 id:'guangxi',
 name:'2024 广西省赛真题卷 · 云计算应用 样卷',
 tag:'省赛线 · 真题原文',
 order:5,
 desc:'广西 2024 省赛样卷（★★★★☆）：私有云 30 + 容器云 30 + 公有云 40。RAID5 磁盘阵列 + RabbitMQ 三级调优 + Redis 主从/Ceph；容器云 MariaDB/Redis/Nginx/Explorer 四镜像 compose 编排 + GitLab CI/CD + Istio 灰度；公有云 ChartMuseum 私有 chart 仓 + WordPress。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《2024 广西省赛题 1~5 套 + 样卷》合集，题库 ZT-16）；小题分值为按结构估计',
 env:'双机虚拟机（controller + compute，CentOS 7.9/openEuler，OpenStack Train 离线包）+ K8s 双节点（master + node）+ 任一国内公有云账号',
 rules:'<b>原文赛制</b>：① 集群模式，每队独立租户，2 名选手账号密码相同 ② x 为赛位号，第二块网卡地址自行创建 ③ 账号资源/竞赛资源包/附件在考位信息表与设备确认单中给出 ④ 自行修改服务器密码 ⑤ 调优/排错题只公布范围不公布赛题。',
 modules:[
 {
  name:'模块一 私有云（30 分 · 建议 80 分钟）',
  minutes:80,
  brief:'<p><b>原文背景</b>：数字化转型，聚焦「DevOps 开发运维一体化」与「数据驱动产品开发」，OpenStack 私有云 + Kubernetes 云原生 + 国内公有云边缘计算。<b>IP 规划（原文表1）</b>：controller/compute eth0 172.129.x.0/24（x=赛位号），eth1 自定义；PC 使用 172.24.16.0/24。</p>',
  tasks:[
  {title:'任务1 · 私有云服务搭建（5 分 · 10 小题）',
   brief:'<p>原文 1.1.1–1.1.10（两处变体已标粗）：</p>',
   checks:[
    {d:'1.1.1 集群主机环境：controller/compute 主机名 + hosts 映射 + yum 源',p:0.5},
    {d:'1.1.2 双节点安装 openstack-iaas 软件包',p:0.5},
    {d:'1.1.3 MariaDB/RabbitMQ 安装与使用',p:0.5},
    {d:'1.1.4 Keystone 安装并创建用户',p:0.5},
    {d:'1.1.5 Glance 安装：上传镜像并设置启动要求参数',p:0.5},
    {d:'1.1.6 Nova 安装与相关配置',p:0.5},
    {d:'1.1.7 Neutron 安装',p:0.5},
    {d:'<b>1.1.8 Dashboard 安装 + Django 数据改为文件存储（变体）</b>',p:0.5},
    {d:'<b>1.1.9 Swift 安装 + cirros 镜像分片存储（变体）</b>',p:0.5},
    {d:'1.1.10 Cinder 安装 + 计算节点块存储扩容',p:0.5}
   ],
   refs:['iaas 系列脚本顺序：base → db/mq → keystone → glance → nova → neutron → dashboard → swift → cinder','Django 文件存储：LOCAL_PATH/SESSION_ENGINE 相关配置','swift 分片：segment-size 上传分段'],
   sol:'与贵州卷同骨架，但 1.1.8/1.1.9 各藏一个小变体——审题时圈出「修改为存储在文件中」「分片存储」两个关键词。'},
  {title:'任务2 · 私有云服务运维（15 分）',
   brief:'<p>原文 1.2.1–1.2.10（<b>RAID 与中间件调优是本卷特色</b>）：</p>',
   checks:[
    {d:'<b>1.2.1 RAID 磁盘阵列：云硬盘分区 + 创建 /dev/md5（RAID5 + 1 热备盘）</b>',p:2},
    {d:'<b>1.2.2 RabbitMQ 调优：用户级/系统级/配置文件三处设置最大连接数</b>',p:1.5},
    {d:'1.2.3 Keystone 优化：增加失效列表缓存时间',p:1.5},
    {d:'1.2.4 Glance 镜像压缩（HTTP 文件服务器中的 CentOS 镜像）',p:1.5},
    {d:'1.2.5 虚拟机调整 Flavor：修改配置使调整实例大小可用',p:1.5},
    {d:'1.2.6 Nova 数据库连接调优：连接池大小 + 最大超出连接数',p:1.5},
    {d:'1.2.7 Heat 模板创建网络',p:1.5},
    {d:'<b>1.2.8 Redis 应用部署：两台云主机配置主从架构</b>',p:2},
    {d:'<b>1.2.9 Ceph 应用部署：安装 ceph 服务并完成初始化</b>',p:1.5},
    {d:'1.2.10 平台调优或排错（范围题：按检查单自证）',p:0.5}
   ],
   refs:['mdadm -C /dev/md5 -l 5 -n 3 -x 1 /dev/vd{b,c,d,e}','ulimit -n / system.conf / rabbitmq.conf 三处连接数','allow_resize_same_host=True + nova-manage','redis 主从：slaveof + masterauth'],
   sol:'RAID5 = n 数据盘 + 1 热备：-n 3 -x 1 共 4 块盘；RabbitMQ「三处」缺一扣分；Ceph 初始化指 mon/osd 就绪。'},
  {title:'任务3 · 私有云运维开发（10 分）',
   brief:'<p>原文 1.3.1–1.3.3：</p>',
   checks:[
    {d:'<b>1.3.1 Ansible 部署 zabbix 监控服务</b>',p:3.5},
    {d:'1.3.2 Python 运维开发：Flavor 增删查改',p:3.5},
    {d:'1.3.3 OpenStack 自动化运维工具（范围题）',p:3}
   ],
   refs:['ansible-playbook zabbix.yml（zabbix-server + zabbix-agent）','python-openstackclient Flavor CRUD 或 shade SDK'],
   sol:'Ansible 题看幂等与跑通；Flavor CRUD 四个操作各占 1 分左右。'}
  ]
 },
 {
  name:'模块二 容器云（30 分 · 建议 70 分钟）',
  minutes:70,
  brief:'<p><b>原文背景</b>：Kubernetes + KubeVirt 管「裸金属/VM/容器」全运行时 + 基于 K8s 的 CI/CD + Istio 灰度发布。<b>本卷特色：四镜像 Dockerfile 全手写 + Explorer 管理系统 compose 编排</b>。</p>',
  tasks:[
  {title:'任务1 · 容器云服务搭建（5 分）',
   brief:'<p>原文 2.1.1：</p>',
   checks:[
    {d:'用 OpenStack 创建两台云主机作 master/node，K8s 集群部署完成',p:2},
    {d:'Istio 服务网格部署',p:1},
    {d:'KubeVirt 虚拟化部署',p:1},
    {d:'Harbor 镜像仓库部署',p:1}
   ],
   refs:['kubeadm init --image-repository … --pod-network-cidr …','istioctl install；kubectl apply -f kubevirt-operator.yaml','harbor 安装包 docker-compose up -d'],
   sol:'一次搭四件：K8s → Istio → KubeVirt → Harbor，顺序别乱。'},
  {title:'任务2 · 容器云服务运维（15 分）',
   brief:'<p>原文 2.2.1–2.2.12（<b>四镜像 + compose 编排是本卷特色</b>）：</p>',
   checks:[
    {d:'<b>2.2.1 Dockerfile 构建 mysql 镜像（centos 基础装 MariaDB + 自启）</b>',p:1},
    {d:'<b>2.2.2 Dockerfile 构建 redis 镜像（centos + 自启）</b>',p:1},
    {d:'<b>2.2.3 Dockerfile 构建 nginx 镜像（centos + 自启）</b>',p:1},
    {d:'<b>2.2.4 Dockerfile 构建 explorer 镜像（centos + PHP + HTTP 环境）</b>',p:1},
    {d:'<b>2.2.5 docker-compose.yaml 编排部署 Explorer（mysql/redis/nginx/explorer）</b>',p:2},
    {d:'2.2.6 GitLab 部署到 kube-ops 命名空间并完成配置',p:1},
    {d:'2.2.7 GitLab Runner 部署到 kube-ops 并注册',p:1},
    {d:'2.2.8 GitLab 新建公开项目导入离线包 + K8s 集群接入 GitLab',p:1},
    {d:'2.2.9 CI/CD 流水线：构建代码→构建镜像→推送 Harbor→发布 K8s',p:2.5},
    {d:'2.2.10 Istio 路由：Bookinfo 默认全走 v1，再按比例从 v1 分流 v3',p:1.5},
    {d:'2.2.11 KubeVirt VMI：default 命名空间创建名为 exam 的 VMI 并用 Service 暴露',p:1.5},
    {d:'2.2.12 容器云平台调优或排错（范围题）',p:0.5}
   ],
   refs:['四个 Dockerfile： centos 基础 + systemctl init 脚本','docker-compose up -d 四服务互联','DestinationRule + VirtualService：reviews weight 比例分流','VMI + Service（spec.ports → vmi 端口）'],
   sol:'四个 Dockerfile 同模板换应用；Explorer 编排注意服务依赖顺序；Istio 灰度看 weight 字段。'},
  {title:'任务3 · 容器云运维开发（10 分）',
   brief:'<p>原文 2.3.1/2.3.2/2.3.3：</p>',
   checks:[
    {d:'2.3.1 K8s Python：管理 Service 资源（增删查改）',p:3.5},
    {d:'2.3.2 K8s Python：管理 Deployment 资源（增删查改）',p:3.5},
    {d:'2.3.3 K8s 自动化运维工具（范围题）',p:3}
   ],
   refs:['kubernetes python client：CoreV1Api / AppsV1Api'],
   sol:'Service 用 CoreV1Api、Deployment 用 AppsV1Api，别混 API 组。'}
  ]
 },
 {
  name:'模块三 公有云（40 分 · 建议 90 分钟）',
  minutes:90,
  brief:'<p><b>原文背景</b>：国内公有云云主机/云网络/云硬盘/云防火墙/负载均衡 + 云原生 DevOps + 云边端一体化边缘计算。<b>本卷特色：ChartMuseum 私有 chart 仓 + WordPress chart 部署 + 弹性伸缩</b>。</p>',
  tasks:[
  {title:'任务1 · 公有云服务搭建（5 分）',
   brief:'<p>原文 3.1.1–3.1.9：</p>',
   checks:[
    {d:'3.1.1 私有网络管理（VPC 创建）',p:0.5},
    {d:'3.1.2 云实例管理（创建两台）',p:0.5},
    {d:'3.1.3 数据库：intnetX-mysql 网络两台 chinaskill-sql 云主机装 MongoDB',p:0.5},
    {d:'3.1.4 MongoDB 主从数据库配置',p:0.5},
    {d:'3.1.5 安全组创建',p:0.5},
    {d:'3.1.6 公网 NAT 网关创建',p:0.5},
    {d:'3.1.7 云服务器备份：存储库 server_backup + 制作镜像 chinaskill-image',p:1},
    {d:'3.1.8 负载均衡器 chinaskill-elb 创建',p:0.5},
    {d:'3.1.9 弹性伸缩启动配置创建',p:0.5}
   ],
   refs:['控制台路径题：VPC/ECS/安全组/NAT/ELB/AS 各模块'],
   sol:'备份题两步（存储库 + 镜像）占 1 分是本组大题。'},
  {title:'任务2 · 公有云服务运维（10 分）',
   brief:'<p>原文 3.2.1–3.2.6（<b>CCE 云容器引擎 + ChartMuseum + WordPress</b>）：</p>',
   checks:[
    {d:'3.2.1 云容器引擎：创建 x86 架构容器云集群',p:2},
    {d:'3.2.2 插件管理安装 Dashboard 可视化监控',p:1.5},
    {d:'3.2.3 安装 kubectl 并操作 kcloud 集群',p:1.5},
    {d:'3.2.4 安装 Helm 包管理器',p:1.5},
    {d:'<b>3.2.5 ChartMuseum：chartmuseum 命名空间 + chartmuseum:latest 镜像建本地私有 chart 仓</b>',p:2},
    {d:'<b>3.2.6 WordPress：用 wordpress-13.0.23.tgz chart 包部署</b>',p:1.5}
   ],
   refs:['helm repo add local http://chartmuseum:8080 …','helm install wp ./wordpress-13.0.23.tgz'],
   sol:'ChartMuseum 本质是一个 Deployment + Service；WordPress 用本地 chart 包 install 即可。'},
  {title:'任务3 · 公有云运维开发（10 分）',
   brief:'<p>原文 3.3.1–3.3.4：</p>',
   checks:[
    {d:'3.3.1 SDK 云主机管理：增删查改',p:3},
    {d:'<b>3.3.2 SDK 云主机组管理：增删查改</b>',p:3},
    {d:'<b>3.3.3 弹性伸缩组 API：Python 创建弹性伸缩组</b>',p:2.5},
    {d:'3.3.4 公有云自动化运维程序开发（范围题）',p:1.5}
   ],
   refs:['官方 SDK：ECS/AS 客户端初始化 → create/delete/list/update'],
   sol:'云主机组（server group）与云主机是两类资源，API 前缀不同。'},
  {title:'任务4 · 边缘计算系统运维（10 分）',
   brief:'<p>原文 3.4.1–3.4.3：</p>',
   checks:[
    {d:'3.4.1 云端部署：KubeEdge CloudCore 就绪并启动',p:3},
    {d:'3.4.2 边端部署：EdgeCore 接入并启动',p:4},
    {d:'3.4.3 边缘应用部署与调试（范围题）',p:3}
   ],
   refs:['keadm init --advertise-address=<云端IP>','keadm join --cloudcore-ipport=<IP>:10000 --token=…'],
   sol:'KubeEdge 云边两命令 + 10000/10002 端口放行。'},
  {title:'任务5 · 边缘计算云应用开发（5 分）',
   brief:'<p>原文 3.5.1：</p>',
   checks:[
    {d:'云应用微服务开发（范围题：边端采数 → 云端可见闭环）',p:5}
   ],
   refs:['MQTT broker + 云端 rule + 应用镜像'],
   sol:'范围题按「能演示的最小闭环」自证。'}
  ]
 }
 ]
};
})();
