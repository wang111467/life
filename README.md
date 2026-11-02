# W 的生活空间

纯 HTML、CSS、JavaScript 小项目。本地启动一次后，添加图片或视频只需刷新网页；GitHub 在线网站在提交文件后自动更新，不用手动修改 `media.js`。

浏览顺序：首页点击「逛逛我的空间」→ 选择「w的提升空间」或「w的健身空间」→ 查看视频或图片。内容页可以返回空间选择，空间选择页可以返回首页。

## 添加视频和图片

把视频放进 `media/videos/`，图片放进 `media/photos/`，支持子文件夹。

**GitHub 网站：**把新增的文件提交到仓库默认分支，GitHub Actions 会自动扫描目录、生成清单并更新网站。等待 Actions 完成后刷新网站即可；删除文件也会自动同步。

**本地使用：**双击「启动生活空间.command」，自动启动本地预览并打开浏览器。以后把图片或视频放进目录，刷新网页或点击页面的「刷新」就会显示；删除文件也会同步。保持启动时的终端窗口打开，不需要重复运行脚本。

本地网址：<http://127.0.0.1:8000>。请通过这个网址访问，直接双击 HTML 只能查看已有静态清单，无法自动发现新增文件。

停止时在终端按 `Ctrl+C`；关闭服务或重启电脑后，下次使用时再次双击启动入口即可。本地服务只监听 `127.0.0.1`，使用 Python 3 标准库，无需安装依赖，不需要把服务部署到 GitHub。

也可以在项目目录运行：

```sh
python3 server.py --open
```

如果 8000 端口被占用，可以改用 `python3 server.py --port 8001 --open`。

视频自动提取 `2026年11月1日` 这样的日期作为标题，默认从新到旧排列；没有有效日期的文件显示原文件名并排在最后。同一天可以用 `2026年11月1日-学习.mp4` 区分多个视频。

图片和视频共用一个全屏查看壳层：点击图片看大图，点击视频直接播放；通过左右按钮或方向键循环切换当前空间内的记录，按 Esc 或右上角关闭按钮返回。图片在手机上还可以左右滑动切换。只有一条记录时，左右按钮会置灰。切换或关闭时会停止旧视频，避免声音继续播放；焦点在视频播放器内时，方向键保留快进、后退功能。

视频推荐 MP4（H.264 + AAC），图片推荐 JPG、PNG、WebP。其他格式能否播放或显示取决于浏览器。

## 放到 GitHub

首次设置：

1. 把整个项目提交到 GitHub，包括 `.github/workflows/pages.yml`、`scripts/`、`assets/` 和 `media/`。
2. 在仓库的 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 在 **Actions** 中运行「更新媒体并发布生活空间」，或者向默认分支提交一次更新。

之后每次提交图片或视频，网站都会自动更新。发布的是生成的 `_site/` 静态目录，网站没有后台服务，所有资源均使用相对路径。GitHub 的首次设置需要在你创建仓库后完成；本项目没有替你创建仓库或发布媒体。

官方说明：[使用 GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 项目文件

```text
index.html       首页和两个空间
styles.css       页面样式
app.js           页面交互、日期标题和排序
viewer.js        图片和视频共用的大图/播放壳层
media.js         自动生成的文件名清单，无需编辑
assets/          本地插画
media/videos/    视频目录
media/photos/    图片目录
启动生活空间.command 本地启动入口（macOS，每次使用时启动一次）
server.py        本地刷新时实时读取媒体目录
scripts/         自动扫描和生成发布文件
.github/         GitHub 自动发布配置
```

开发验证：`python3 -m unittest discover -s tests -v`。手动生成发布目录：`python3 scripts/build_media.py --deploy`。
