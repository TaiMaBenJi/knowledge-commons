# -*- coding: utf-8 -*-
"""第 18 集 · 云计算从零到精通（总纲片）

全系列的「地图集」：从最底层的服务器，一路走到云原生与架构决策。
分镜脚本与 video-factory/scripts/course-*.py 同构（EPISODE dict），
额外支持 visual='clip:<name>' 字段标记「AI 生成的电影级镜头」，
由 build/build_ep18.py 用 AI 片段替换静帧。
"""

EPISODE = {
    'id': '18',
    'sid': 'course',
    'disp': '18',
    'series': '云计算保姆级教程 · 从零到精通',
    'title': '云计算从零到精通（总纲片）',
    'slides': [

        # ---------- 0 · 封面 ----------
        {
            'type': 'cover',
            'title': '云计算\n从零到精通',
            'subtitle': '总纲片 · 一部讲清整张地图',
            'items': [
                '这是一张地图：每一层是什么、彼此怎么咬合、你要走到哪一层',
                '零基础也能看完 · 看完就知道下一步该学什么',
            ],
            'narration': '这是整个云计算系列的总纲片。如果你刚接触云计算，接下来这十几分钟，会给你一张完整的地图——从最底层的服务器，一直走到云原生和架构决策。如果你已经会一点也没关系，我们把散落的知识点重新串成一条线，看清楚每一层之间到底是什么关系。',
        },

        # ---------- 1 · 钩子（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'dc_corridor',
            'title': '你正在看的这条视频，其实不在你手机上',
            'narration': '先问你一个问题：现在这一刻，你正在看的这条视频，是在哪儿被播放的？不在你的手机里。手机只负责显示。真正解码、真正传输、真正存储这些画面的，是某个数据中心里成百上千台服务器。',
        },

        # ---------- 2 · 冲击数据 ----------
        {
            'type': 'bignums',
            'title': '你手机里的每一个 App，背后都是一座矿场',
            'accent': (56, 189, 248),
            'nums': [
                {'num': '60', 'unit': '+', 'd': '个 App 同时在线\n每个背后都是一片服务器'},
                {'num': '24', 'unit': 'h', 'd': '全年无休\n没有一天在下班'},
                {'num': '200', 'unit': 'ms', 'd': '点一次支付\n必须在这个时间内返回'},
            ],
            'narration': '你手机里那几十个 App，背后可能是几千台机器在同时工作。刷短视频要撑住千万级并发，外卖要扛住饭点瞬时洪峰，支付要在两百毫秒内给出结果。这不是一家公司做得到几万台的规模——是成千上万家公司的机器，被同一个"云"调度在了一起。',
        },

        # ---------- 3 · 破除神秘感（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'city_phone',
            'title': '"云"一点都不玄',
            'narration': '这就是云计算最反直觉的地方："云"一点都不玄。它不是飘在天上的魔法，它就是别人机房里的电脑。只不过你不用买、不用搬、也不用维护，需要的时候，按分钟租走，用完就还。',
        },

        # ---------- 4 · 三个问题 ----------
        {
            'type': 'steps',
            'title': '要理解云计算，先回答三个问题',
            'accent': (251, 191, 36),
            'steps': [
                {'t': '"云"到底是什么？', 'd': '它凭什么比"自己买"划算'},
                {'t': '你到底租走了什么？', 'd': '从裸金属到函数的五层楼'},
                {'t': '从零开始，这条路怎么走？', 'd': '一条可执行的阶段路线'},
            ],
            'narration': '要理解云计算，只要先回答三个问题：第一，"云"到底是什么，它凭什么比"自己买"划算；第二，你到底租走了什么；第三，从零开始，这条路该怎么走。',
        },

        # ---------- 5 · 拥有 vs 租用 ----------
        {
            'type': 'compare',
            'title': '云的第一性原理：把"拥有"换成"租用"',
            'left': {
                't': '过去：拥有',
                'accent': (248, 113, 113),
                'items': [
                    '买服务器、装系统、配网络',
                    '找机房托管，一套下来好几万',
                    '容量按"最忙那天"买',
                    '还要有人天天盯着',
                ],
            },
            'right': {
                't': '现在：租用',
                'accent': (52, 211, 153),
                'items': [
                    '控制台点一下，几十秒开好',
                    '按小时计费，随时增减',
                    '多节点可以拉出成百上千台',
                    '机房、电力、硬件都归厂商管',
                ],
            },
            'narration': '我们先看第一问。云的本质，是把"拥有"换成了"租用"。过去你想跑一个网站，得自己买服务器、装系统、配网络、找机房托管，一套下来几万块，还得有人盯着。但云把这一整套动作收成了一条：控制台点一下，几十秒，一台机器就跑起来了。省下的不只是钱，是那些本该花在重复劳动上的时间。',
        },

        # ---------- 6 · 硬技术（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'cloud_particles',
            'title': '租用成立，靠的是三件硬技术',
            'narration': '但"租用"之所以能成立，靠的不是云厂商的良心，是三件硬技术：虚拟化、网络，和规模。这三件东西，恰好是计算机工业一百年来最成熟的三件事。',
        },

        # ---------- 7 · 三支柱 ----------
        {
            'type': 'bullets',
            'title': '三根支柱，撑起了整个"云"',
            'accent': (167, 139, 250),
            'items': [
                {'t': '虚拟化：一台物理机，切成很多台虚拟电脑', 'd': '每台都以为自己独占了全部硬件'},
                {'t': '网络：把这些电脑连成一片，像一台巨大的机器', 'd': '这才是"云"和"一堆铁盒子"的区别'},
                {'t': '规模：几十万几百万台一起采购、一起运维', 'd': '单位成本被摊薄到几乎可以忽略'},
            ],
            'narration': '虚拟化，让一台物理机变成很多台看起来完全独立的电脑；网络，让这些电脑连成一片，像一台巨大的机器；规模经济，让几十万、几百万台机器的采购和运维成本，摊薄到几乎可以忽略。三件事凑齐，"租用"才真的比"拥有"划算。',
        },

        # ---------- 8 · 五级台阶（脊柱） ----------
        {
            'type': 'ladder',
            'title': '从零到精通，其实是五级台阶',
            'subtitle': '今天我们就从下到上，把每一层都走一遍',
            'narration': '弄懂了"云"是什么，我们来看第二问：你到底租走了什么。其实从零到精通，就是五级台阶。今天我们从下到上，把这五级每一层都走一遍，看清楚它们之间是怎么咬合的。',
        },

        # ---------- 9 · L1（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'rack_wall',
            'title': 'L1 地基层 · 所有云最终都跑在实体机上',
            'narration': '第一级，地基层。所有云上的东西，最终都落在一台实实在在的电脑上——CPU、内存、硬盘、网卡，再加一个操作系统。这一层要学的是 Linux 和网络：进程、权限、文件、服务、端口、路由。听起来枯燥，但它是唯一一层不会过时的知识。',
        },

        # ---------- 10 · L1 清单 ----------
        {
            'type': 'table',
            'title': 'L1 地基层：真正要掌握的就这几样',
            'accent': (56, 189, 248),
            'headers': ['模块', '要会什么', '为什么重要'],
            'rows': [
                ['Linux 基础', '目录/权限/进程/服务/日志', '云上 90% 的操作都在敲命令'],
                ['网络基础', 'IP、子网、端口、DNS、TCP', '排障第一步就是看网络通不通'],
                ['存储概念', '块存储/文件存储/对象存储', '选错类型，数据结构就错了'],
                ['机房常识', '机柜、供电、制冷、容灾', '决定你能理解到多深'],
            ],
            'narration': '具体一点，这一层要掌握的东西其实很有限：命令行的日常操作、文件的属主和权限、进程和服务的启停，还有网络——IP、子网、端口、DNS、TCP。实际工作里，九成的"云的问题"排查到最后，都落在这几样上面。',
        },

        # ---------- 11 · L1 的价值 ----------
        {
            'type': 'bullets',
            'title': 'L1 为什么值得花最多时间',
            'accent': (52, 211, 153),
            'items': [
                {'t': '它是唯一不会过时的层', 'd': 'K8s 会换版本，Linux 不会'},
                {'t': '它是所有故障的最终落点', 'd': '"服务起不来"最后永远是 Linux 问题'},
                {'t': '它是面试最常问的层', 'd': '问得最多，也最容易答出深度'},
            ],
            'narration': '为什么要在这一层花最多时间？三个理由：它是唯一不会过时的一层，Kubernetes 会换版本，Linux 不会；它是所有故障的最终落点，"服务起不来"追到最后永远是 Linux 的问题；它也是面试问得最多的一层。地基越稳，上面每一层都越不用操心。',
        },

        # ---------- 12 · L2（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'virtualization',
            'title': 'L2 虚拟化 · 把一台大机器切成很多台',
            'narration': '第二级，虚拟化。假设机房里有六十四核 CPU、五百多 G 内存的物理机，如果只跑一个业务，剩下的资源就白白扔了。虚拟化做的事情，是把这台机器"切"成很多台虚拟的机器，每一台都以为自己独占了全部硬件。',
        },

        # ---------- 13 · L2 三件事 ----------
        {
            'type': 'bullets',
            'title': '虚拟化的三个关键词',
            'accent': (251, 191, 36),
            'items': [
                {'t': 'Hypervisor：做切分的那个软件', 'd': 'KVM、VMware ESXi 都在这一层'},
                {'t': '虚拟机：切出来的每一份', 'd': '每份都有自己独立的操作系统'},
                {'t': '虚拟化漏洞：隔离的底层机制', 'd': '靠软件特权级转换实现，效率极高'},
            ],
            'narration': '理解这层，你就能想明白两个很常见的困惑。第一，为什么云主机比裸金属贵一点——因为你买的是"随时可切、随时可退"的灵活性。第二，为什么云主机的性能不会永远满血——隔壁邻居的负载，会通过共享物理资源影响到你。这就是所谓的"吵闹邻居"问题。',
        },

        # ---------- 14 · 虚拟机 vs 容器 ----------
        {
            'type': 'compare',
            'title': '虚拟机切的是硬件，容器切的是操作系统',
            'left': {
                't': '虚拟机 VM',
                'accent': (248, 113, 113),
                'items': [
                    '带完整操作系统，隔离强',
                    '启动慢，通常几十秒',
                    '一台物理机通常只跑几个',
                    '体积大，几 GB 起',
                ],
            },
            'right': {
                't': '容器 Container',
                'accent': (52, 211, 153),
                'items': [
                    '共享宿主机内核，隔离稍弱',
                    '启动快，秒级',
                    '一台物理机能跑几十上百个',
                    '体积小，几十 MB 起',
                ],
            },
            'narration': '既然有虚拟机，为什么全世界都在用容器？因为容器切的是操作系统，不是硬件。虚拟机每台都带一整套操作系统，启动要几十秒，一台物理机通常只跑得下几个；容器共享宿主机内核，启动是秒级的，一台机器能塞下几十上百个。代价是隔离没有虚拟机强，所以金融级隔离还得靠虚拟机。',
        },

        # ---------- 15 · 容器编排（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'containers',
            'title': 'L4 容器编排 · 云原生的心脏',
            'narration': '于是有了编排器。镜像负责把应用打包成不可变的一份，容器负责把它跑起来，Kubernetes 负责决定它跑在哪台机器上、坏了换一个、多了加几个、流量怎么分。全套东西合起来，就是"云原生"这个词的实体。',
        },

        # ---------- 16 · IaaS/PaaS/SaaS ----------
        {
            'type': 'table',
            'title': 'L3 服务模型：你到底管到哪一层',
            'accent': (167, 139, 250),
            'headers': ['层级', '厂商给你什么', '你要自己管什么'],
            'rows': [
                ['IaaS', '虚拟机、硬盘、网络', '操作系统、中间件、应用、数据'],
                ['PaaS', '运行时、数据库、消息队列', '你的应用代码和数据'],
                ['SaaS', '开箱即用的完整软件', '只用，浏览器打开就能用'],
            ],
            'narration': '第三级，也是最常被问的一个：服务模型。云服务商把服务切成三档。IaaS 给你虚拟机和存储，操作系统往上你全得自己管；PaaS 给你运行时和数据库，你只写代码；SaaS 是成品软件，浏览器打开就能用。',
        },

        # ---------- 17 · 怎么选 ----------
        {
            'type': 'compare',
            'title': '选型只有一条原则',
            'left': {
                't': '离业务代码远',
                'accent': (56, 189, 248),
                'items': [
                    '团队只想"用"一套系统',
                    '预算和人力都有限',
                    '选 SaaS，别自己造轮子',
                ],
            },
            'right': {
                't': '离业务代码近',
                'accent': (52, 211, 153),
                'items': [
                    '要写自己的系统、要改逻辑',
                    '需要控制运行时和数据',
                    '选 PaaS 或 IaaS',
                ],
            },
            'narration': '怎么选？记住一句话：离你的业务代码越近，越选 PaaS；离你的业务代码越远，越选 IaaS；压根不写代码，直接 SaaS。比方说你要做一个自己的系统，那必然是 PaaS 或 IaaS；如果你只是想让同事用一套报销系统——直接 SaaS，别自己开发。绝大多数"上云"失败的项目，都是在这张表上选错了行。',
        },

        # ---------- 18 · 弹性（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'elasticity',
            'title': 'L5 弹性 · 云最值钱的一个词',
            'narration': '第四级，弹性。云计算最值钱的一个词，就是"按需伸缩"。平时十台机器够用，促销那晚来一万个用户，扩容到一百台；活动结束，再缩回十台。资源像水电一样开关，这才是云和传统机房最本质的区别——传统机房买的是"峰值容量"，一年里只有一天用得上，剩下的时间全是浪费。',
        },

        # ---------- 19 · 无服务器的边界 ----------
        {
            'type': 'bullets',
            'title': 'Serverless 很美，但有明确边界',
            'accent': (248, 113, 113),
            'items': [
                {'t': '适合：事件驱动、流量起伏极大', 'd': '图片处理、Webhook、定时任务'},
                {'t': '不适合：长任务、重计算、有稳定状态', 'd': '冷启动和执行时长上限会拖垮它'},
                {'t': '真正要判断的是"要不要有状态"', 'd': '这一步想清楚，选型就清楚了'},
            ],
            'narration': '再往上，还有 Serverless——你连机器都不用管了，只交一个函数，有人调用就跑，没人调用就停，按调用次数计费。听起来很美，但它有明确的适用边界：不是所有系统都适合。尤其是长任务、重计算、有稳定状态的应用，冷启动和执行时长上限会直接拖垮它。',
        },

        # ---------- 20 · 精通（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'earth_nodes',
            'title': '第五级 · 走到精通',
            'narration': '第五级，走到精通。你会发现，前面那些名词——虚拟化、容器、编排、弹性——其实都不是终点。它们服务的，是四个更重要的目标。',
        },

        # ---------- 21 · 精通四维 ----------
        {
            'type': 'table',
            'title': '精通之后，你每天在权衡的四件事',
            'accent': (251, 191, 36),
            'headers': ['维度', '核心动作', '翻车时的样子'],
            'rows': [
                ['安全', '最小权限、加密、密钥管理、审计', '密钥裸奔、权限全开'],
                ['可靠', '多可用区、故障转移、备份与演练', '单点故障、备份从没恢复过'],
                ['成本', '按需付费、利用率优化、预算告警', '月底账单吓到老板'],
                ['可观测', '指标、日志、链路追踪、告警', '出事没人知道，用户先知道'],
            ],
            'narration': '安全，指的是身份和最小权限、传输和静态加密、密钥管理、审计合规；可靠，指的是多可用区部署、故障自动转移、备份和灾备演练；成本，指的是按需付费、资源利用率优化、预算告警，以及最容易被忽略的出网流量费；可观测，指的是指标、日志、链路追踪三件套，以及出事时告警能不能真的叫醒人。这四件事，才是架构师每天真正在权衡的东西。',
        },

        # ---------- 22 · 三个转变 ----------
        {
            'type': 'bignums',
            'title': '从零到精通，你真正发生的变化',
            'accent': (167, 139, 250),
            'nums': [
                {'num': '1', 'unit': '.', 'd': '从记住名词\n到理解机制'},
                {'num': '2', 'unit': '.', 'd': '从会搭起来\n到搭得稳'},
                {'num': '3', 'unit': '.', 'd': '从完成需求\n到对成本和风险负责'},
            ],
            'narration': '从零到精通，你真正发生的变化，其实是三个转变：从"记住名词"到"理解机制"，从"会搭起来"到"搭得稳"，从"完成需求"到"对成本和风险负责"。第三个转变最慢，也最值钱——它决定了你是一个执行者，还是一个能拍板的人。',
        },

        # ---------- 23 · 学习路线 ----------
        {
            'type': 'steps',
            'title': '一条可以照着走的路线',
            'accent': (52, 211, 153),
            'steps': [
                {'t': '第一阶段 · 打地基', 'd': 'Linux + 网络 + 虚拟化原理，2~4 周'},
                {'t': '第二阶段 · 上真云', 'd': '选一家（AWS/阿里云/腾讯云），亲手用一遍核心服务'},
                {'t': '第三阶段 · 云原生', 'd': 'Docker + K8s，把一个真实小项目部署上去'},
                {'t': '第四阶段 · 像架构师', 'd': 'IaC、CI/CD、可观测、成本控制与风险预案'},
            ],
            'narration': '所以，如果你想走这条路，给你一条可执行的路线。第一阶段，把 Linux 和网络打牢，同时理解虚拟化是怎么回事。第二阶段，选一个云平台——AWS、阿里云、腾讯云都行——把计算、存储、数据库、网络、安全组亲手用一遍。第三阶段，上容器和 Kubernetes，把一个真实的小项目部署上去。第四阶段，补上基础设施即代码、持续交付、可观测性和成本控制，开始像个架构师一样思考。',
        },

        # ---------- 24 · 收尾（AI 镜头） ----------
        {
            'type': 'clip',
            'clip': 'dawn_server',
            'title': '没有捷径，但也不需要天赋',
            'narration': '这条路上没有捷径，但也不需要天赋。需要的只是：把每一层都亲手搭过一次，把每一个坑都自己踩一遍。',
        },

        # ---------- 25 · 金句 ----------
        {
            'type': 'note',
            'text': '云计算不是背名词，\n是把"拥有"换成"租用"，\n把"手工"换成"自动"，\n把"能用"换成"敢托付"。',
            'sub': '——把这四句话刻在脑子里，整条路就通了',
            'accent': (56, 189, 248),
            'narration': '如果今天只能记住四句话，就是这四句：云计算不是背名词，是把"拥有"换成"租用"，把"手工"换成"自动"，把"能用"换成"敢托付"。',
        },

        # ---------- 26 · 结尾 ----------
        {
            'type': 'end',
            'kicker': '第 18 集 · 总纲片 · 完',
            'title': '从第 0 集开始\n把这条线走完',
            'sub': '零基础 13 集 · 教程 19 集 · 进阶 29 集 · 机房专项 15 集 · 世赛总纲课 50 集',
            'next': '配套图文教程 + 真机训练场（wsarena）· 全部免费',
            'narration': '这是整个系列的总纲片。接下来每一集，都会把今天这条线上的某一层，掰开揉碎讲透。零基础学堂十三集、教程十九集、进阶二十九集、机房专项十五集，再加上各赛项的总纲课，一共一百二十多集视频课，配上配套图文和真机训练场，全部免费。从第零集开始，跟着走就行。我们下一集见！',
        },
    ],
}

# AI 镜头清单：name -> 分镜提示词
CLIPS = {
    'dc_corridor': 'Cinematic wide shot down a long data center corridor at night, two rows of black server racks with dense cyan and amber indicator LEDs, cold blue volumetric haze, polished dark floor with subtle reflections, dramatic overhead light strips, shallow depth of field, photorealistic, 35mm anamorphic, no text, no people, no logos',
    'city_phone': 'Cinematic night cityscape seen from above, a single hand holding a glowing smartphone in the lower foreground, warm bokeh city lights, distant glass data center building with lit windows, teal and amber color grade, photorealistic, shallow depth of field, 50mm, no text, no logos, no visible brand',
    'cloud_particles': 'Abstract dark visualization of cyan and blue luminous particles flowing and converging into a coherent swirling cloud form, deep navy void background, soft volumetric glow, thin light trails, elegant minimal tech aesthetic, cinematic motion, no text, no people, no logos',
    'rack_wall': 'Cinematic frontal view of a vast server rack wall in a dark data hall, hundreds of identical blade servers with dense blinking status lights, cool cyan wash with warm amber accents, deep perspective corridor, atmospheric haze, photorealistic, 24mm, no text, no people, no logos',
    'virtualization': 'Cinematic conceptual shot: one large glowing monolithic server block splitting apart into many smaller luminous rectangular units floating in dark space, thin cyan energy lines connecting them, dark navy background, volumetric light, elegant minimal 3D render, no text, no people, no logos',
    'containers': 'Cinematic overhead-angled view of many standardized glowing shipping-container-like blocks neatly stacked and being rearranged by invisible machinery in a dark industrial space, cyan edge lighting, amber accents, volumetric haze, photorealistic 3D render, no text, no people, no logos',
    'elasticity': 'Cinematic split-time visualization of a data center floor: the left half dim and mostly empty racks, the right half fully lit and packed with busy servers, a smooth gradient of light traveling across the frame, deep teal to warm amber transition, photorealistic, wide shot, no text, no people, no logos',
    'earth_nodes': 'Cinematic view of Earth at night from orbit, dark blue continents, a network of glowing cyan light nodes and thin arcs connecting cities, subtle atmospheric rim light, deep space star field, photorealistic, ultra detailed, no text, no logos',
    'dawn_server': 'Cinematic sunrise seen through the glass wall of a data center cold aisle, warm golden light flooding in over rows of dark server racks, lens flare, dust motes in the light beams, calm and hopeful mood, photorealistic, 35mm, no text, no people, no logos',
}
