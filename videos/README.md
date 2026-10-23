# videos/ —— 视频课资产（**布局是构建契约，别重排**）

仓库里所有视频课与封面都放这里，站点页面、客户端打包、CI 工作流都按这个布局取文件。

## 目录

```
videos/
├── ep01.mp4 … ep15.mp4    # 「机房/使用指南」系列 15 集（历史落位，保持在根目录）
├── course/                # 教程 19 集 + course/covers/ 19 张封面
├── ext/                   # 进阶 29 集 + ext/covers/ 29 张封面
├── beginner/              # 零基础学堂 13 集（epb1.mp4 …，learn/beginner.html 引用）
├── gallery/               # 逐集图解截图（90 张，video-ext/01-图解册.md 配图）
├── covers/                # 根级 ep*.mp4 的封面 15 张
└── README.md              # 本文件
```

合计 63 集视频课（机房 15 + 教程 19 + 进阶 29）＋ 零基础学堂 13 集 ＋ 世赛总纲课（在 `multiskill/` 各赛项目录下）。

## 谁在引用（改名前必查）

| 引用方 | 引用方式 |
|---|---|
| `viewer.html` | `src` 以 `videos/` 开头的路径**原样保留**，配合 `docs/**` 里的讲义 Markdown |
| `learn/beginner.html` | `../videos/beginner/epb<集号>.mp4`（动态拼串） |
| `.github/workflows/embed-course-videos.yml` | `ls videos/*.mp4`、`videos/course/*.mp4`、`videos/ext/*.mp4` 计数校验 |
| `.github/workflows/upload-training-videos.yml` | 上传训练视频 |
| `clients/*/build_ci.sh` | 整目录 `cp -R videos/` 打进各端安装包 |

## 生成方式

视频由 `video-factory/` 流水线产出（脚本 + 课件源在同目录）；单集：

```sh
python3 video-factory/build_episode.py video-factory/scripts/beginner-b1.py
```

产出后按上面的布局落位，再 bump `sw.js` 的 `VERSION`。
