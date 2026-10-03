# Tianzheng Miao · Personal research lab

深色科技实验室风的个人学术主页。纯静态 HTML、CSS 和 JavaScript，适合直接部署到 GitHub Pages；不需要 Node、npm 或后端。

## 预览

在项目目录运行：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8000>。也可以直接打开 `index.html`；本地文件模式下，剪贴板能力取决于浏览器权限。

## 更新内容

编辑 `data/site.json`，然后运行：

```powershell
python tools/build.py
python tools/check_site.py
```

把生成的 HTML 和 `citations/` 文件一起提交。GitHub Pages 直接发布这些静态文件，不需要在线运行 Python。

| 内容 | 数据位置 |
| --- | --- |
| 姓名、邮箱、照片、简介 | `profile` |
| 研究方向及首页项目 | `projects` |
| 论文、作者、链接和引用 | `publications` |
| 教育经历 | `education` |
| 奖项 | `awards` |
| 审稿和委员会经历 | `services` |
| 置顶研究方向 | `focus` |
| 随笔、研究日志 | `posts` |
| GNN 项目图示及数据集 | `gnn` |

增加论文时，在 `publications` 添加对象，使用唯一 `id`。年份、筛选和 BibTeX 文件自动生成。添加随笔时，在 `posts` 添加唯一 `id`、ISO 日期 `YYYY-MM-DD`、`title`、`lang`、`tags` 和 `paragraphs`；首页显示最新两篇，归档页自动倒序排列，标签也会自动更新。

现有研究详情保留原 URL。新建详情页时，在 `tools/build.py` 添加渲染函数和 `pages` 条目，并将 `projects` 中的 `slug` 指向它。所有页面通过 `templates/base.html` 共用导航、页脚和元数据。

## 修改样式和交互

- `jemdoc.css`：统一设计系统，顶部变量控制主题色、字体和背景；包含移动端、减少动态效果和打印适配。
- `main.js`：网络示意图、主题切换、移动菜单、搜索筛选、引用复制、图片放大与随笔深链接。
- `theme.js`：在页面绘制前恢复主题偏好；默认深色。
- `templates/base.html`：所有页面的公共骨架。
- `tools/build.py`：仅使用 Python 标准库的静态生成器。

完整内容预先生成在 HTML 中，禁用 JavaScript 仍能阅读文章、浏览论文、下载 BibTeX 并查看原图。网络图为概念示意；连线变化不代表实测速率或仿真结果。字体在 `fonts/` 本地托管，附带 SIL OFL 许可证；加载失败时自动使用系统字体。大型测试床照片使用 WebP 预览，放大时仍可查看原始 PNG。

`MENU` 和 `jemdoc.py` 为历史文件，当前页面使用 `tools/build.py` 维护。
