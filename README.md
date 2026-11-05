# Tianzheng Miao · Academic homepage

传统学术主页风格：白底、衬线正文、单栏、以文字和论文为主。纯静态 HTML 和 CSS，只有研究页的互动示意图（`network.js`）和首页的鲨鱼横幅（`sharks/ascii-sharks.js`）用到 JavaScript，适合直接部署到 GitHub Pages；不需要 Node、npm 或后端。

## 预览

在项目目录运行：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8000>，也可以直接双击 `index.html`。

## 更新内容

编辑 `data/site.json`，然后运行：

```powershell
python tools/build.py
python tools/check_site.py
```

把生成的 HTML 和 `citations/` 文件一起提交。GitHub Pages 直接发布这些静态文件，不需要在线运行 Python。不要直接改生成的 `.html`，下次构建会覆盖。

| 内容 | 数据位置 |
| --- | --- |
| 姓名、职位、地址、邮箱、照片 | `profile` |
| 首屏的一句话研究简介 | `profile.research_intro` |
| 职位下方的 secondment 说明（支持 `[文字](网址)` 链接） | `profile.secondment` |
| 首页 About 段落（支持 `[文字](网址)` 链接）、Research Perspective 段落、研究兴趣 | `profile.about`、`profile.perspective`、`profile.interests` |
| 研究方向（首页列表及详情页入口） | `projects` |
| 论文、作者、链接和 BibTeX | `publications` |
| 工作经历（首页 Experience） | `experience` |
| 教育经历 | `education` |
| 奖项 | `awards` |
| 审稿和委员会经历 | `services` |
| GNN 研究页：摘要、关键结果、图示 | `gnn` |

增加论文时，在 `publications` 添加对象，使用唯一 `id`；论文页按年份自动分组，BibTeX 展示和 `citations/*.bib` 文件自动生成。`doi` 以 `10.48550/` 开头（arXiv）时不在正文显示，仅通过 arXiv 链接给出。

现有研究详情页保留原 URL。新建详情页时，在 `tools/build.py` 添加渲染函数和 `pages` 条目，并将 `projects` 中的 `slug` 指向它。所有页面共用 `templates/base.html`（导航、页脚、元数据）。页脚的年份和 “Last updated” 取构建当天的日期。

## 修改样式

- `style.css`：全部样式。顶部 `:root` 变量控制颜色、字体和页面宽度（`--page`，宽屏左栏宽度 `--rail`）。宽度不小于 56rem 时，章节标题和照片放在左栏、正文在右栏；更窄的屏幕自动变为单栏。
- `fonts/`：Source Serif 4 本地托管（SIL OFL 许可证在同目录）；加载失败时自动使用系统衬线字体。中文内容使用系统无衬线字体。
- `templates/base.html`：所有页面的公共骨架。
- `tools/build.py`：仅使用 Python 标准库的静态生成器。`tools/check_site.py`：检查本地链接、锚点、资源、标题层级、图片描述和 BibTeX 文件。

页面包含打印样式，可直接打印或另存为 PDF。

### 设计方向与来源

本次精修参考 [unslop](https://github.com/heydamir/unslop)，作者 [Damir Sokolovsky (@heydamir)](https://x.com/heydamir)，采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。按已有学术风格调整，保留白底、蓝色链接、Source Serif 4、章节顺序和左侧索引栏。

- 间距与布局：以 4px 为间距步长，统一章节、研究条目和论文列表的留白；正文在桌面保持可读宽度，手机姓名与小幅肖像并排。
- 色彩与字体：保留原配色，用正文、次要信息和元数据三种层级组织内容；姓名、论文标题依靠字号区分，减少粗体和斜体强调。
- 文案与入口：首屏研究简介取自已有个人介绍；增加研究和论文直达链接，不改动论文题名或研究事实。
- 视觉与交互：保留真实肖像和 ASCII 鲨鱼，将横幅压缩为 120px；动画默认静止，支持手动播放、暂停和系统减少动态效果设置；链接和控件提供键盘焦点状态。

## 互动示意图

`cellfree.html`（默认系统视图）和 `cellfree-gnn.html`（默认二部图视图）各有一张根据论文画的示意图：天花板 AP、前传、CPU（H → W），以及 GNN 使用的 AP–用户二部图。可拖动用户（也可用键盘方向键）、点选节点高亮其链路、切换视图，并分三步演示“输入 H → 逐层更新边特征 → 输出 W”。链路粗细只是随距离变化的示意，不是实测数据。

- 图的结构和坐标：`tools/build.py` 里的 `NETWORK`（AP、用户的数量与位置）和 `network_figure()`；改完重新构建即可。
- 交互逻辑：`network.js`；图的样式：`style.css` 中 “Interactive network figure” 一节。
- 不启用 JavaScript 时，页面仍显示完整的静态图和说明，只是没有按钮。
- 在别的页面放这张图：在对应的渲染函数里调用 `network_figure(编号, 'system' 或 'graph')`，构建脚本会自动为该页面引入 `network.js`。

## 首页鲨鱼横幅

首页顶部保留 120px 高的 ASCII 鲨鱼横幅，默认显示静态画面。点击 “Play animation” 后，鲨鱼追逐鱼群，点击横幅会惊散鱼群；“Pause animation” 可暂停。来自 [stackedlol/ascii-sharks](https://github.com/stackedlol/ascii-sharks)（MIT，许可证见 `sharks/LICENSE`）：上游的 TypeScript 源码去掉类型标注后合成了一个普通脚本 `sharks/ascii-sharks.js`，本地补充了播放和暂停控制。

- 鲨鱼品种和大小：`tools/build.py` 里的 `SHARKS`。第一个最大，后面依次缩小；可选 `classic`、`hammerhead`、`greathammer`、`tiger`、`zebra`、`mako`、`thresher`、`nurse`。改完重新构建即可。
- 横幅高度和样式：`style.css` 中 “Home: ASCII shark banner” 一节。打印时不显示。
- 横幅滚出屏幕时暂停动画；系统开启“减少动态效果”时只显示一帧静止画面，并隐藏播放按钮。

`MENU` 和 `jemdoc.py` 为历史文件，当前页面使用 `tools/build.py` 维护。
