/* =====================================================================
   全真模拟卷 · 2023 安徽省职业院校技能大赛（高职组）云计算应用赛项 任务书样题
   依据：公开赛卷原文（CSDN wangchuan_yyd，题库 ZT-18 全文，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文（粗粒度任务书式）：
   私有云50（搭建10/运维25/开发15）+ 容器云50（搭建10/运维25/开发15）。
   特点：安徽特色「大分值粗粒度」——每题只给能力域不给逐条命令，
   适合练「任务书阅读 + 自证清白」（自己定验收标准、自己留证据）。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['anhui']={
 id:'anhui',
 name:'2023 安徽省赛真题卷 · 云计算应用 任务书样题',
 tag:'省赛线 · 真题原文',
 order:5,
 desc:'安徽 2023 省赛任务书样题（★★★☆☆）：私有云 50（搭建10/运维25/开发15）+ 容器云 50（搭建10/运维25/开发15）。与逐条小题的广东/贵州/河北/广西/江西不同，本卷是「大分值粗粒度」任务书——练阅读拆解与自证留痕的最佳卷。',
 source:'公开赛卷原文摘录（CSDN wangchuan_yyd《2023 安徽任务书样题》全文，题库 ZT-18）；原文仅给能力域与分值，评分细项按能力域拆解估计',
 env:'双机虚拟机（controller + compute，CentOS 7.9/openEuler，OpenStack Train 离线包）+ K8s 集群 + Harbor + Prometheus',
 rules:'<b>任务书要诀</b>：① 原文只给「做什么」不给「怎么做」——先花 10 分钟把大题拆成自己的子任务清单再动手 ② 应用部署类（博客系统/应用商城）必须留可访问地址截图 ③ 排错题自查证据链：改了什么、为什么、怎么验证 ④ 调优排错题只公布范围不公布赛题。',
 modules:[
 {
  name:'模块一 私有云（50 分 · 建议 120 分钟）',
  minutes:120,
  brief:'<p><b>原文背景</b>：OpenStack 私有云 + Kubernetes 云原生 + 国内公有云边缘计算。<b>IP 规划（原文表1）</b>：controller/compute eth0 172.129.x.0/24（x=赛位号），eth1 自定义。<b>本卷特色：按「安装脚本框架补全」方式搭建</b>——不是白手起家，而是补完给定的半成品脚本。</p>',
  tasks:[
  {title:'任务1 · 私有云服务搭建（10 分）',
   brief:'<p>原文三条要求：① 登录集群云平台用镜像创建两台云主机并保证网络互通，按要求配置服务器安装基础服务 ② 按提供的安装脚本框架补充完成 OpenStack 平台各服务组件部署 ③ 用 OpenStack 命令检测平台和服务运行状态。</p>',
   checks:[
    {d:'云主机创建 + 网络互通 + 基础服务配置',p:3},
    {d:'按脚本框架补全 OpenStack 各组件部署（keystone/glance/nova/neutron/dashboard/storage 全链）',p:5},
    {d:'命令行检测平台与服务运行状态并留存输出',p:2}
   ],
   refs:['先通读脚本框架：哪些段是空的、哪些参数要填','openstack service list / nova service-list / neutron agent-list 三件套自检'],
   sol:'「补全脚本」与「从头装」是两种功：先看懂框架再动笔，别推倒重来。'},
  {title:'任务2 · 私有云服务运维（25 分）',
   brief:'<p>原文三条要求：① 对平台及各组件运维管理：云主机、云存储、云网络、云数据库、负载均衡和高可用 ② 完成私有云应用项目部署：私有博客系统、应用商城网站等 ③ 分析排查平台、云服务、云应用系统的问题。</p>',
   checks:[
    {d:'云主机/云存储/云网络运维（实例、卷、网络/子网/路由操作各留证据）',p:8},
    {d:'云数据库 + 负载均衡 + 高可用运维（创建/配置/验证）',p:7},
    {d:'私有博客系统部署并可访问',p:5},
    {d:'应用商城网站部署并可访问',p:5}
   ],
   refs:['数据库：mariadb/redis 类；负载均衡：octavia/lbaas 成员与监听','博客：WordPress/Typecho 任一；商城：gpmall 类','每项运维操作 systemctl status + curl 验证截图'],
   sol:'25 分大头在「运维面广」：把六个能力域各做一小块并留痕，比深耕一个域得分高。'},
  {title:'任务3 · 私有云运维开发（15 分）',
   brief:'<p>原文两条要求：① 用 Ansible 进行自动化运维开发 ② 用 Python 调用 OpenStack APIs 与 SDK 完成云平台日常运维。</p>',
   checks:[
    {d:'Ansible 自动化运维开发（playbook 可跑 + 幂等）',p:7},
    {d:'Python 调用 OpenStack APIs（接口直调）',p:4},
    {d:'Python 调用 OpenStack SDK（日常运维脚本）',p:4}
   ],
   refs:['ansible：inventory + playbook + 幂等回放','keystone token → REST API；openstacksdk 连接脚本'],
   sol:'APIs（HTTP）与 SDK（库）两条路都要展示，别只交一份。'}
  ]
 },
 {
  name:'模块二 容器云（50 分 · 建议 120 分钟）',
  minutes:120,
  brief:'<p><b>原文背景</b>：Docker/Harbor/Kubernetes + istio + KubeVirt + Prometheus。<b>本卷特色：Docker CE/compose/Harbor 与 K8s 系并列在同一个搭建题里</b>，且要求「导入给定镜像并推送私有仓库」。</p>',
  tasks:[
  {title:'任务1 · 容器云服务搭建（10 分）',
   brief:'<p>原文两条要求：① Docker CE、docker-compose、Harbor 仓库安装，导入给定镜像并推送私有仓库 ② Kubernetes 平台、istio、KubeVirt、Prometheus 部署，用命令检测容器云平台和服务运行状态。</p>',
   checks:[
    {d:'Docker CE + docker-compose + Harbor 安装',p:3},
    {d:'导入给定镜像并推送私有仓库（tag + push + 页面可见）',p:2},
    {d:'Kubernetes 平台部署（节点 Ready）',p:3},
    {d:'istio + KubeVirt + Prometheus 部署',p:1.5},
    {d:'命令检测容器云平台与服务状态并留存输出',p:0.5}
   ],
   refs:['docker load → tag → docker login → push','kubectl get nodes/cs/pods -A 三件套自检'],
   sol:'「推送到私有仓库」必须验到 Harbor 页面或 API 列表，只 push 不验证容易丢分。'},
  {title:'任务2 · 容器云服务运维（25 分）',
   brief:'<p>原文三条要求：① 对 Kubernetes 平台、istio、KubeVirt 各组件运维管理：Pod、Deployment、Service、Ingress、网络、存储卷和 Istio 服务网格 ② 用提供的应用程序基于 Docker 编排部署应用系统；按给定架构构建 CI/CD 环境并配置持续集成 ③ 分析排查容器云平台、云服务、云应用的系统问题。</p>',
   checks:[
    {d:'Pod/Deployment/Service/Ingress 运维（扩缩容/更新/暴露）',p:8},
    {d:'网络 + 存储卷 + Istio 服务网格运维',p:6},
    {d:'Docker 编排部署给定应用系统',p:5},
    {d:'CI/CD 环境构建 + 持续集成服务配置（提交触发构建）',p:6}
   ],
   refs:['kubectl scale/set image/rollout','PVC + StorageClass；Istio DestinationRule/VirtualService','Jenkins/GitLab + webhook 触发记录'],
   sol:'CI/CD 单独 6 分——流水线要真触发一次并留构建日志，搭好不触发等于没做。'},
  {title:'任务3 · 容器云运维开发（15 分）',
   brief:'<p>原文要求：基于 Kubernetes 集群，使用 Python 编写脚本调用 Kubernetes APIs 与 SDK，实现对容器云平台的管理和运维。</p>',
   checks:[
    {d:'Python 调用 K8s APIs（Restful 直调：认证 + 资源操作）',p:7},
    {d:'Python 调用 K8s SDK（kubernetes client 管理运维脚本）',p:8}
   ],
   refs:['ServiceAccount token + requests 直打 apiserver','from kubernetes import client, config'],
   sol:'15 分整块给开发：APIs 路与 SDK 路各交一套脚本，输出要有人能看懂的结果。'}
  ]
 }
 ]
};
})();
