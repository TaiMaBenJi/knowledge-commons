/* =====================================================================
   全真模拟卷 · 2024 河北省职业院校技能大赛 云计算应用赛项 赛题第 1 套
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-14 五套合集之第 1 套，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文：
   私有云50（搭建10/运维25/开发15）+ 容器云50（搭建5/运维30/开发15）。
   特点：运维与开发分值比国赛更重（容器云运维高达 30 分）——适合练
   「部署速度 + 运维模板」的组合功。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['hebei']={
 id:'hebei',
 name:'2024 河北省赛真题卷 · 云计算应用 赛题第 1 套',
 tag:'省赛线 · 真题原文',
 order:3,
 desc:'河北 2024 省赛第 1 套（★★★★☆）：私有云 50（搭建10/运维25/开发15）+ 容器云 50（搭建5/运维30/开发15）。运维题量大是本卷特色：SkyWalking、Heat、镜像压缩、监控四件套、CI/CD 一次练全。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《2024 河北省赛题 1~5 套》合集，题库 ZT-14）；小题分值为按结构估计',
 env:'双机虚拟机（controller + compute，CentOS 7.9/openEuler，OpenStack Train 离线包）+ K8s 三节点离线包',
 rules:'<b>省赛要诀</b>：① 本卷运维 25+30=55 分——运维模板的熟练度决定胜负 ② 搭建 10+5=15 分要在 50 分钟内拿下 ③ 每道运维题都含「做出来 + 验出来」两层分 ④ 调优排错题只公布范围。',
 modules:[
 {
  name:'模块一 私有云（50 分 · 建议 120 分钟）',
  minutes:120,
  brief:'<p><b>原文背景</b>：企业数字化转型，OpenStack 私有云平台（与贵州卷同源企业背景）。</p>',
  tasks:[
  {title:'任务1 · 私有云服务搭建（10 分）',
   brief:'<p>标准搭建链（原文任务1）：</p>',
   checks:[
    {d:'基础环境：双机主机名 + hosts 映射 + yum 源',p:1},
    {d:'双节点安装 openstack-iaas 软件包',p:1},
    {d:'MariaDB/RabbitMQ 安装与调优',p:1},
    {d:'Keystone 安装并创建用户',p:1},
    {d:'Glance 安装；上传镜像并设置启动参数',p:1},
    {d:'Nova 双端安装与配置',p:1},
    {d:'Neutron 双端安装',p:1},
    {d:'Dashboard 安装',p:0.5},
    {d:'Swift 安装',p:0.5},
    {d:'Cinder 安装；计算节点块存储扩容',p:0.5},
    {d:'全链验证：可创建云主机并可访问',p:1}
   ],
   refs:['iaas 系列脚本：base→db/mq→keystone→glance→nova→neutron→dashboard→swift→cinder','openstack compute service list'],
   sol:'11 小题 10 分——比贵州卷多出全链验证分，创建云主机必须真正可访问。'},
  {title:'任务2 · 私有云服务运维（25 分）',
   brief:'<p>运维八连（原文 1.2.1–1.2.8）：</p>',
   checks:[
    {d:'1.2.1 Linux 网络命名空间运维（ip netns 创建/连通验证）',p:3},
    {d:'1.2.2 Glance 开放镜像权限（指定项目共享）',p:3},
    {d:'1.2.3 Glance 镜像压缩（qemu-img convert -c）',p:3},
    {d:'1.2.4 Nova 清除缓存',p:3},
    {d:'1.2.5 Glance 对接 Cinder 存储',p:3},
    {d:'1.2.6 Heat 模板创建存储容器',p:3},
    {d:'1.2.7 SkyWalking 应用部署（ES + APM + 应用接入）',p:3.5},
    {d:'1.2.8 平台调优或排错（范围题：按检查单自证）',p:4}
   ],
   refs:['ip netns add ns1；openstack image add-project …','qemu-img convert -c；nova-manage …','SkyWalking：elasticsearch + skywalking-oap + skywalking-ui'],
   sol:'25 分大题——每题的验证动作就是分；SkyWalking 三件套部署是本卷最耗时项，建议先装。'},
  {title:'任务3 · 私有云运维开发（15 分）',
   brief:'<p>原文 1.3.1/1.3.2：</p>',
   checks:[
    {d:'1.3.1 OpenStack 用户管理（脚本化管理用户/项目/配额）',p:7},
    {d:'1.3.2 平台自动化运维工具（范围题：巡检/报表/告警）',p:8}
   ],
   refs:['openstack user/project/quota 系列 + python 巡检脚本'],
   sol:'开发 15 分——脚本要能跑、能演示、输出规范。'}
  ]
 },
 {
  name:'模块二 容器云（50 分 · 建议 110 分钟）',
  minutes:110,
  brief:'<p>原文模块二：kubeadm 平台 + 监控四件套 + Jenkins/GitLab + Istio/KubeVirt。运维 30 分为本系列最高。</p>',
  tasks:[
  {title:'任务1 · 容器云服务搭建（5 分）',
   brief:'<p>原文 2.1.1：</p>',
   checks:[
    {d:'kubeadm 集群就绪（节点 Ready、CNI 正常）',p:4},
    {d:'私有镜像仓库可用（集群可拉取）',p:1}
   ],
   refs:['kubeadm init --image-repository … --pod-network-cidr …'],
   sol:'搭建只有 5 分但必须快——把时间省给运维 30 分。'},
  {title:'任务2 · 容器云服务运维（30 分）',
   brief:'<p>原文 2.2.1–2.2.12（12 项全考）：</p>',
   checks:[
    {d:'2.2.1 容器化部署 Node-Exporter 数据采集器',p:2.5},
    {d:'2.2.2 容器化部署 Alertmanager 告警服务器',p:2.5},
    {d:'2.2.3 容器化部署 Grafana 可视化分析工具',p:2.5},
    {d:'2.2.4 容器化部署 Prometheus 云原生监控系统',p:3},
    {d:'2.2.5 编排部署 Prometheus 监控系统（清单联动）',p:2.5},
    {d:'2.2.6 安装 Jenkins',p:2},
    {d:'2.2.7 安装 GitLab',p:2},
    {d:'2.2.8 Jenkins 与 GitLab 集成',p:2.5},
    {d:'2.2.9 构建 CI/CD 环境',p:3},
    {d:'2.2.10 服务网格：创建 Ingress Gateway',p:2.5},
    {d:'2.2.11 KubeVirt 运维：创建 VM',p:2.5},
    {d:'2.2.12 容器云平台调优或排错（范围题）',p:2.5}
   ],
   refs:['监控四件套 → kube-prometheus 编排 → Jenkins/GitLab → istio gateway → kubevirt vmi','kubectl get pods -A 全绿为验收基线'],
   sol:'12 项 30 分——平均每项 2.5 分，拼的是「每项都做到位」而不是单点深挖；建议按 2.2.1→2.2.5 顺序一次成型。'},
  {title:'任务3 · 容器云运维开发（15 分）',
   brief:'<p>原文 2.3.1/2.3.2：</p>',
   checks:[
    {d:'2.3.1 自定义调度器（schedulerName 指定并验证）',p:7},
    {d:'2.3.2 K8s 平台自动化运维工具（范围题）',p:8}
   ],
   refs:['第二调度器 Deployment + 测试 Pod + NodeName 绑定验证'],
   sol:'调度器要「看得见效果」：Pod 确实被你的调度器调度。'}
  ]
 }
 ]
};
})();
