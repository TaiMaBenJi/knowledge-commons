/* =====================================================================
   全真模拟卷 · 2024 贵州省职业院校技能大赛 云计算应用赛项 赛题第 1 套
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-15 六套合集之第 1 套，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文：
   私有云30（搭建5/运维15/开发10）+ 容器云30（搭建5/运维15/开发10）+
   公有云40（搭建5/运维10/开发10/边缘运维10/边缘开发5）。
   特点：私有云含 Manila 前身链路精简版、SkyWalking、MongoDB 主从（公有云）。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['guizhou']={
 id:'guizhou',
 name:'2024 贵州省赛真题卷 · 云计算应用 赛题第 1 套',
 tag:'省赛线 · 真题原文',
 order:4,
 desc:'贵州 2024 省赛第 1 套（★★★☆☆，入门到进阶过渡卷）：私有云 30 + 容器云 30 + 公有云 40。容器云四大监控件 + Jenkins/GitLab/CI-CD 全家桶 + Istio/KubeVirt，公有云 MongoDB 主从 + KubeEdge 边缘计算。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《2024 贵州省赛题 1~6 套》合集，题库 ZT-15）；小题分值为按结构估计',
 env:'双机虚拟机（controller + compute，CentOS 7.9/openEuler，OpenStack Train 离线包）+ K8s 三节点 + 任一国内公有云账号',
 rules:'<b>原文赛制</b>：① 集群模式，每队独立租户，2 名选手账号密码相同 ② x 为赛位号，第二块网卡地址自行创建 ③ 账号资源/竞赛资源包/附件在考位信息表与设备确认单中给出 ④ 自行修改服务器密码 ⑤ 调优/排错题只公布范围不公布赛题。',
 modules:[
 {
  name:'模块一 私有云（30 分 · 建议 80 分钟）',
  minutes:80,
  brief:'<p><b>原文背景</b>：企业数字化转型，OpenStack 私有云 + Kubernetes 云原生 + 国内公有云边缘计算。<b>IP 规划（原文表1）</b>：controller/compute eth0 172.129.x.0/24（x=赛位号），eth1 自定义。</p>',
  tasks:[
  {title:'任务1 · 私有云服务搭建（5 分 · 10 小题）',
   brief:'<p>原文 1.1.1–1.1.10：</p>',
   checks:[
    {d:'1.1.1 集群主机环境：controller/compute 主机名 + hosts 映射 + yum 源',p:0.5},
    {d:'1.1.2 双节点安装 openstack-iaas 软件包',p:0.5},
    {d:'1.1.3 MariaDB/RabbitMQ 安装与使用',p:0.5},
    {d:'1.1.4 Keystone 安装并创建用户',p:0.5},
    {d:'1.1.5 Glance 安装与使用',p:0.5},
    {d:'1.1.6 Nova 安装',p:0.5},
    {d:'1.1.7 Neutron 安装',p:0.5},
    {d:'1.1.8 Dashboard 安装',p:0.5},
    {d:'1.1.9 Swift 安装',p:0.5},
    {d:'1.1.10 Cinder 创建硬盘',p:0.5}
   ],
   refs:['iaas 系列脚本顺序：base → db/mq → keystone → glance → nova → neutron → dashboard → swift → cinder','openstack service list 逐项验证'],
   sol:'标准搭建链，无 Manila/Dashboard 文件化等变体——本卷最"纯"的送分链，适合练速度。'},
  {title:'任务2 · 私有云服务运维（15 分）',
   brief:'<p>原文 1.2.1–1.2.8：</p>',
   checks:[
    {d:'1.2.1 Linux 网络命名空间运维（ip netns 创建/验证）',p:2},
    {d:'1.2.2 Glance 开放镜像权限（共享给指定项目）',p:2},
    {d:'1.2.3 Glance 镜像压缩（qemu-img convert -c）',p:2},
    {d:'1.2.4 Nova 清除缓存',p:2},
    {d:'1.2.5 Glance 对接 Cinder 存储',p:2},
    {d:'1.2.6 Heat 模板创建存储容器（heat-swift 类）',p:2},
    {d:'1.2.7 SkyWalking 应用部署并监控 gpmall 类应用',p:2},
    {d:'1.2.8 平台调优或排错（范围题：按检查单自证）',p:1}
   ],
   refs:['ip netns add ns1 && ip netns exec ns1 ip a','openstack image add-project …','qemu-img convert -O qcow2 -c in.qcow2 out.qcow2'],
   sol:'运维面与国赛同源；SkyWalking 需要 ES + APM 两件套，注意 JVM 内存参数。'},
  {title:'任务3 · 私有云运维开发（10 分）',
   brief:'<p>原文 1.3.1/1.3.2：</p>',
   checks:[
    {d:'1.3.1 OpenStack 用户管理脚本（创建/列表/配额）',p:5},
    {d:'1.3.2 平台自动化运维工具（范围题：巡检/报表/告警任选）',p:5}
   ],
   refs:['openstack user create …；python3 openstack 巡检脚本'],
   sol:'脚本评分看「能跑 + 覆盖范围 + 输出规范」，写完当场演示。'}
  ]
 },
 {
  name:'模块二 容器云（30 分 · 建议 70 分钟）',
  minutes:70,
  brief:'<p>原文模块二：kubeadm 容器云平台 + 监控四件套 + Jenkins/GitLab + Istio/KubeVirt。</p>',
  tasks:[
  {title:'任务1 · 容器云服务搭建（5 分）',
   brief:'<p>原文 2.1.1：</p>',
   checks:[
    {d:'kubeadm 集群就绪（节点 Ready、CNI 正常）',p:4},
    {d:'私有镜像仓库可用（集群可拉取）',p:1}
   ],
   refs:['kubeadm init --image-repository … --pod-network-cidr …'],
   sol:'闭卷 40 分钟内出活集群；离线包 + containerd 两处配置必改。'},
  {title:'任务2 · 容器云服务运维（15 分）',
   brief:'<p>原文 2.2.1–2.2.12：</p>',
   checks:[
    {d:'2.2.1-4 容器化部署 Node-Exporter / Alertmanager / Grafana / Prometheus',p:4},
    {d:'2.2.5 编排部署 Prometheus 云原生监控系统（数据贯通）',p:2},
    {d:'2.2.6 安装 Jenkins',p:1},
    {d:'2.2.7 安装 GitLab',p:1},
    {d:'2.2.8 Jenkins 与 GitLab 集成（凭据/webhook）',p:1.5},
    {d:'2.2.9 构建 CI/CD 环境（提交→构建→部署）',p:2},
    {d:'2.2.10 Istio：创建 Ingress Gateway（网格入口可用）',p:1.5},
    {d:'2.2.11 KubeVirt 运维：创建 VM（实例 Running）',p:1.5},
    {d:'2.2.12 容器云平台调优或排错（范围题）',p:0.5}
   ],
   refs:['kubectl apply -f kube-prometheus/…','istioctl install && kubectl apply -f gateway.yaml','kubectl apply -f vmi.yaml'],
   sol:'监控四件套按依赖顺序部署；KubeVirt 先 operator 后 VM。'},
  {title:'任务3 · 容器云运维开发（10 分）',
   brief:'<p>原文 2.3.2/2.3.3（本套无 2.3.1）：</p>',
   checks:[
    {d:'2.3.2 自定义调度器（schedulerName 指定并验证调度）',p:5},
    {d:'2.3.3 K8s 平台自动化运维工具（范围题）',p:5}
   ],
   refs:['schedulerName: my-scheduler；第二调度器 Deployment + NodeName 绑定'],
   sol:'自定义调度器最低可行实现 + 测试 Pod 验证。'}
  ]
 },
 {
  name:'模块三 公有云（40 分 · 建议 90 分钟）',
  minutes:90,
  brief:'<p>原文模块三：公有云资源交付 + <b>MongoDB 主从</b>（本卷特色）+ 运维开发 + KubeEdge 边缘计算。</p>',
  tasks:[
  {title:'任务1 · 公有云服务搭建（5 分）',
   brief:'<p>原文 3.1.1–3.1.8：</p>',
   checks:[
    {d:'3.1.1 私有网络管理（VPC/子网）',p:1.5},
    {d:'3.1.2 云实例管理',p:1.5},
    {d:'3.1.6 安全组管理',p:1},
    {d:'3.1.8 NAT 网关（私网出网）',p:1}
   ],
   refs:['控制台路径题：网络→VPC；计算→ECS；安全组按题放行'],
   sol:'路径题背路径，做完即验。'},
  {title:'任务2 · 公有云服务运维（10 分）',
   brief:'<p>原文 3.2.1–3.2.3：</p>',
   checks:[
    {d:'3.2.1 管理云 MongoDB 数据库（创建/连接）',p:4},
    {d:'3.2.2 MongoDB 主从数据库（主从关系建立并验证）',p:4},
    {d:'3.2.3 公有云上云及优化（范围题）',p:2}
   ],
   refs:['云数据库控制台：创建 → 白名单 → 主从/副本集'],
   sol:'MongoDB 主从验证用 rs.status() 或控制台主从标识。'},
  {title:'任务3 · 公有云运维开发（10 分）',
   brief:'<p>原文 3.3.1–3.3.3：</p>',
   checks:[
    {d:'3.3.1 开发环境搭建（SDK/CLI/IDE 就绪）',p:2.5},
    {d:'3.3.1b 安全组管理（SDK 创建安全组）',p:2.5},
    {d:'3.3.2 安全组规则管理（规则增删查）',p:2.5},
    {d:'3.3.3 公有云自动化运维程序开发（范围题）',p:2.5}
   ],
   refs:['pip install 官方 SDK；安全组创建/规则增删脚本'],
   sol:'SDK 题按官方 quickstart 改参数；每个操作打日志。'},
  {title:'任务4 · 边缘计算系统运维（10 分）',
   brief:'<p>原文 3.4.1–3.4.3：</p>',
   checks:[
    {d:'3.4.1 云端部署（cloudcore 就绪）',p:3},
    {d:'3.4.2 边端部署（edgecore 接入，边缘节点 Ready）',p:4},
    {d:'3.4.3 边缘应用部署（应用调度到边缘并可访问）',p:3}
   ],
   refs:['keadm init --advertise-address=<云端IP>','keadm join --cloudcore-ipport=<IP>:10000 --token=…'],
   sol:'KubeEdge 云边两命令 + 10000/10002 端口放行 + nodeSelector。'},
  {title:'任务5 · 边缘计算云应用开发（5 分）',
   brief:'<p>原文 3.5：</p>',
   checks:[
    {d:'边缘数据采集应用部署并上报云端可见',p:3},
    {d:'云端下发控制/规则生效（端到端验证）',p:2}
   ],
   refs:['MQTT broker + 云端 rule'],
   sol:'最小闭环：边端模拟数据 → 上报 → 云端可见。'}
  ]
 }
 ]
};
})();
