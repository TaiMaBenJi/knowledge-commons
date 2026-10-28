/* =====================================================================
   全真模拟卷 · 2025 广东省职业院校技能大赛（高职组）“云计算应用”技能测试样题（四）
   依据：公开赛卷原文（CSDN qq_50377269，题库 ZT-12 全文，
   见 docs/contest/真题题库-21套.md）。任务结构忠实原文（2025 新四模块制）：
   私有云25（部署5/运维10/开发10）+ 容器云25（部署5/运维10/开发10）+
   边缘计算20（系统部署运维10/云服务开发10）+ 智能计算20（部署运维10/云服务开发10）。
   特点：Ollama/DeepSeek/Gradio 大模型智能计算 + KubeEdge/FastAPI 边缘计算，
   代表 2025 最新命题方向；原文小题不配分，小题分值按结构估计。
   ===================================================================== */
(function(){
window.KC_PAPERS=window.KC_PAPERS||{};
window.KC_PAPERS['guangdong2025']={
 id:'guangdong2025',
 name:'2025 广东省赛真题全真卷 · 云计算应用 样题（四）',
 tag:'省赛真题卷',
 order:5.5,
 desc:'广东 2025 样题（四）（★★★★★，最新命题方向卷）：私有云 25 + 容器云 25 + 边缘计算 20 + 智能计算 20。2025 新四模块制——KubeEdge/FastAPI 边缘计算 + Ollama/DeepSeek/Gradio 大模型智能体应用，全库唯一自带「智能计算」模块的全真卷。',
 source:'公开赛卷原文摘录（CSDN qq_50377269《2025 广东省“云计算应用”技能测试样题（四）》全文，题库 ZT-12）；原文小题不配分，小题分值按结构估计',
 env:'OpenStack 私有云（controller + compute，http 离线 yum 源）+ K8s 双节点（master + node）+ Istio/KubeVirt/Harbor + KubeEdge 云边环境 + Ollama 大模型环境',
 rules:'<b>原文赛制</b>：① 集群模式，每队独立租户，4 名参赛选手账号密码相同 ② x 为赛位号，OpenStack 第二块网卡地址根据题意自行创建 ③ 按图表检查硬件连线与网络设备配置，确保网络正常 ④ 账号资源/竞赛资源包/附件在考位信息表与设备确认单中给出 ⑤ 自行修改服务器密码，提交时确认 IP/用户名/密码。',
 modules:[
 {
  name:'模块一 私有云（25 分 · 建议 65 分钟）',
  minutes:65,
  brief:'<p><b>原文背景</b>：企业数字化、智能化转型，OpenStack 私有云 + Kubernetes 云原生 + KubeEdge 边缘计算 + DeepSeek 开源大模型智能计算。<b>本模块</b>：私有云平台搭建、运维与自动化运维程序开发（云主机/云网络/云存储基础服务）。</p>',
  tasks:[
  {title:'任务1 · 私有云服务部署（5 分）',
   brief:'<p>原文 1.1.1–1.1.13：</p>',
   checks:[
    {d:'1.1.1-2 主机名 controller/compute + hosts 映射 + 双节点 yum 源 http.repo',p:0.5},
    {d:'1.1.3-4 controller 无秘钥访问 compute + 双节点安装 openstack-iaas',p:0.5},
    {d:'1.1.5 MariaDB/RabbitMQ 安装与调优',p:0.5},
    {d:'1.1.6 Keystone 安装并创建用户',p:0.5},
    {d:'1.1.7 Glance 安装、上传镜像并设置启动要求参数',p:0.5},
    {d:'1.1.8 Nova 双节点安装与相关配置',p:0.5},
    {d:'1.1.9 Neutron 双节点正确安装',p:0.5},
    {d:'1.1.10 Dashboard 安装 + Django 数据改为存储在文件中',p:0.5},
    {d:'1.1.11 Swift 安装 + cirros 镜像分片存储',p:0.5},
    {d:'1.1.12-13 Cinder 安装 + 计算节点块存储扩容 + KVM 启用 virtio-net-pci 调优',p:0.5}
   ],
   refs:['docs/tutorial/20-锐捷云平台基础-试题A实战.md：iaas 脚本链 base → db/mq → keystone → glance → nova → neutron → dashboard → swift → cinder','openstack service list / nova service-list / neutron agent-list 自检'],
   sol:'1.1.10 Django 文件化与 1.1.11 镜像分片是本卷新变体：SESSION_ENGINE 改 file、swift 上传时分片。'},
  {title:'任务2 · 私有云服务运维（10 分）',
   brief:'<p>原文 1.2.1–1.2.10：</p>',
   checks:[
    {d:'1.2.1 Heat 模板 create_user.yaml 创建 heat-user 用户',p:1},
    {d:'1.2.2 Heat 模板完成网络创建',p:1},
    {d:'1.2.3 Linux 系统调优：临时调整回写磁盘时间',p:1},
    {d:'1.2.4 Glance 调优：配置子进程数量',p:1},
    {d:'1.2.5 Redis 应用部署：两台云主机配置 redis 主从架构',p:1},
    {d:'1.2.6 使用 ceph.tar.gz 安装 ceph 服务并完成初始化',p:1},
    {d:'1.2.7 云主机安装部署 MinIO 并用 systemctl 管理',p:1},
    {d:'1.2.8 Glance 调优：子进程数量配置修改为 2',p:1},
    {d:'1.2.9 nova.conf 内存预留量配置为 4GB',p:1},
    {d:'1.2.10 Nova 数据库连接池大小与最大允许超出连接数改为 10',p:1}
   ],
   refs:['heat create_user.yaml：resource_registry OS::Keystone::User','redis 主从：slaveof + masterauth；ceph-deploy / ceph.tar.gz 初始化','vm.overcommit_memory、dirty_ratio 类回写参数；glance-api workers；reserved_host_memory_mb=4096；max_pool_size/ max_overflow=10'],
   sol:'十道运维小题各 1 分、面广量足：Heat 两连 + Redis 主从 + Ceph + MinIO 三部署 + 五处调优，按检查单逐项留痕。'},
  {title:'任务3 · 私有云运维开发（10 分）',
   brief:'<p>原文两条要求：</p>',
   checks:[
    {d:'1.3.1 OpenStack Python 运维开发：实现镜像增删查改',p:5},
    {d:'1.3.2 编写 OpenStack 云平台自动化运维工具',p:5}
   ],
   refs:['python-glanceclient / openstacksdk 镜像 CRUD 脚本','docs/tutorial/13-自动化运维-保姆级.md：巡检/报表类运维工具'],
   sol:'镜像 CRUD 四个操作都要演示；自动化运维工具写出可跑入口 + 输出。'}
  ]
 },
 {
  name:'模块二 容器云（25 分 · 建议 65 分钟）',
  minutes:65,
  brief:'<p><b>原文背景</b>：Kubernetes 容器云集群 + 引入 KubeVirt 实现虚拟化统一管理（裸金属/VM/容器一套调度）+ CI/CD（DevOps）+ Istio 服务网格灰度发布。部署平台用私有云上创建的两台云主机。</p>',
  tasks:[
  {title:'任务1 · 容器云服务部署（5 分）',
   brief:'<p>原文 2.1.1：</p>',
   checks:[
    {d:'私有云上创建 master/node 两台云主机',p:1},
    {d:'Kubernetes 集群部署（节点 Ready）',p:2},
    {d:'Istio 服务网格部署',p:1},
    {d:'KubeVirt 虚拟化部署',p:0.5},
    {d:'Harbor 镜像仓库部署',p:0.5}
   ],
   refs:['kubeadm init + CNI；istioctl install','kubevirt operator；docker-compose/Harbor 离线安装'],
   sol:'K8s 双节点 2 分是大头；Istio/KubeVirt/Harbor 装完各验一句命令。'},
  {title:'任务2 · 容器云服务运维（10 分）',
   brief:'<p>原文 2.2.1–2.2.12：</p>',
   checks:[
    {d:'2.2.1-4 容器化部署监控四件套（Node-Exporter/Alertmanager/Grafana/Prometheus 四个 Dockerfile，基于 centos，开机自启）',p:2},
    {d:'2.2.5 docker-compose.yaml 编排部署监控系统',p:1},
    {d:'2.2.6 default 命名空间部署 Jenkins（持久化存储 + 离线插件 + 登录信息）',p:1},
    {d:'2.2.7 配置 Jenkins Slave（Kubernetes 云 + 容器模板/Pod 模板/标签）',p:0.5},
    {d:'2.2.8 default 命名空间部署 GitLab（新建公开项目并上传代码）',p:1},
    {d:'2.2.9 RabbitMQ + Nacos 部署并完成 Nacos 配置管理',p:1},
    {d:'2.2.10 构建 CI/CD：声明式 Pipeline 触发构建（编译 → 构建镜像推 Harbor → 自动发布 K8s）',p:2},
    {d:'2.2.11 服务网格 Sidecar 管理：default 部署 Bookinfo + exam 命名空间 Sidecar 流量配置',p:1},
    {d:'2.2.12 KubeVirt 创建 VM exam（指定内存/CPU/运行策略/启动参数）',p:0.5}
   ],
   refs:['四个 Dockerfile + docker-compose.yaml 模板','Jenkins kubernetes 插件 Pod Template；GitLab webhook + Jenkinsfile','Bookinfo + Sidecar 资源限制 egress/ingress；kubectl apply vmi-exam.yaml'],
   sol:'CI/CD 2 分须真触发一次：编译 → 镜像 → Harbor → K8s 发布全链留日志；Bookinfo 是 Sidecar 题的固定靶场。'},
  {title:'任务3 · 容器云运维开发（10 分）',
   brief:'<p>原文三条要求（Kubernetes Python 运维脚本开发）：</p>',
   checks:[
    {d:'2.3.1 Python 脚本管理 Service 资源',p:3},
    {d:'2.3.2 Python 脚本管理 Pod 服务',p:3},
    {d:'2.3.3 编写 Kubernetes 容器云平台自动化运维工具',p:4}
   ],
   refs:['from kubernetes import client, config：CoreV1Api service/pod 操作','docs/tutorial/11-Kubernetes入门-保姆级.md'],
   sol:'Service 与 Pod 两套脚本分开交；运维工具给可演示入口。'}
  ]
 },
 {
  name:'模块三 边缘计算（20 分 · 建议 55 分钟）',
  minutes:55,
  brief:'<p><b>原文背景</b>：构建 Kubernetes 容器云平台并部署 KubeEdge，云端 CloudCore + 边侧 EdgeCore，完成应用场景镜像部署与调试；再用 FastAPI 开发边缘计算云应用微服务。<b>本模块是 2025 新增模块</b>，与旧三模块制卷的最大差异之一。</p>',
  tasks:[
  {title:'任务1 · 边缘计算系统部署与运维（10 分）',
   brief:'<p>原文要求：云端部署 KubeEdge CloudCore 云侧模块并启动 cloudcore 服务；边侧部署 EdgeCore 边侧模块并启动 edgecore 服务；通过边缘计算平台完成应用场景镜像部署与调试。</p>',
   checks:[
    {d:'云端部署 CloudCore 并启动 cloudcore 服务',p:4},
    {d:'边侧部署 EdgeCore 并启动 edgecore 服务（边缘节点接入集群）',p:4},
    {d:'应用场景镜像部署与调试（应用调度到边缘节点运行）',p:2}
   ],
   refs:['keadm init --advertise-address=<云端IP>','keadm join --cloudcore-ipport=<IP>:10000 --token=…','边缘 Pod：nodeSelector / tolerations 调度到边缘节点'],
   sol:'云边两命令 + 10000/10002 端口放行；验证 kubectl get nodes 看到边缘节点 Ready 再部署应用。'},
  {title:'任务2 · 边缘计算云服务开发（10 分）',
   brief:'<p>原文要求：基于 FastAPI 框架，实现对接边缘计算云应用微服务开发。</p>',
   checks:[
    {d:'FastAPI 微服务开发（服务可运行、接口可访问）',p:6},
    {d:'微服务对接边缘计算云应用联调（数据/接口端到端验证）',p:4}
   ],
   refs:['pip install fastapi uvicorn；@app.get/post 接口编写','uvicorn 启动 + curl 验证 + 边缘数据上报联调'],
   sol:'FastAPI 六分看「能跑 + 接口规范」；联调四分留端到端证据（边端数据 → 云端接口可见）。'}
  ]
 },
 {
  name:'模块四 智能计算（20 分 · 建议 55 分钟）',
  minutes:55,
  brief:'<p><b>原文背景</b>：构建人工智能 ollama 大模型框架，导入 qwen、deepseek 等开源大模型并验证；基于 ollama 接口用 Gradio 框架调用开源大模型开发智能体应用。<b>本模块是全库独有考点</b>——大模型智能计算正式进赛卷。</p>',
  tasks:[
  {title:'任务1 · 智能计算系统部署与运维（10 分）',
   brief:'<p>原文要求：构建人工智能 ollama 大模型框架，导入 qwen、deepseek 等开源大模型，并验证。</p>',
   checks:[
    {d:'ollama 大模型框架构建（服务可用）',p:4},
    {d:'导入 qwen 开源大模型并验证推理',p:3},
    {d:'导入 deepseek 开源大模型并验证推理',p:3}
   ],
   refs:['ollama serve + systemctl 托管','ollama pull qwen / deepseek-run 逐个 ollama run 验证对话'],
   sol:'部署四分验证服务端口与 ollama list；两个模型各三分，import 后必须真跑一次推理留输出。'},
  {title:'任务2 · 智能计算云服务开发（10 分）',
   brief:'<p>原文要求：基于 ollama 的接口，使用 Gradio 框架，调用开源大模型，开发智能体应用。</p>',
   checks:[
    {d:'基于 ollama 接口 + Gradio 框架调用开源大模型（Web 界面可用）',p:5},
    {d:'智能体应用开发（对话/推理功能完整演示）',p:5}
   ],
   refs:['pip install gradio；gr.Interface/gr.ChatInterface + ollama api（/api/generate 或 /api/chat）','python app.py 启动 → 浏览器访问 → 对话截图'],
   sol:'Gradio 界面调通 ollama 接口即得基本分；智能体分看功能完整度——多轮对话/系统提示词写进应用再演示。'}
  ]
 }
 ]
};
})();
