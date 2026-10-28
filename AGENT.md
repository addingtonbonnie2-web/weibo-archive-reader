# AGENT.md — 给 AI 助手的部署说明

> 写给自动化助手，以及第一次接触这个项目的开发者。人类用户请看 [README.md](README.md)。

## 这是什么

一个本地运行的 Flask 网页应用，把 weibo-crawler 导出的 SQLite 微博库渲染成可浏览的站点。
单进程，默认端口 5055。

服务本身不向外发请求；只有本地缺图时，页面里会写入新浪图床的图片地址，由浏览器去加载。

## 环境

| 项 | 要求 |
|---|---|
| Python | 3.9 及以上（开发环境为 3.13） |
| 依赖 | `flask` / `pillow` / `jieba`（见 requirements.txt） |
| 系统 | Windows 优先（带 .bat）；Linux / macOS 直接 `python run.py` |
| 数据库 | 不需要，demo 脚本会生成一个 |

## 从零跑起来

```bash
cd <仓库目录>
pip install -r requirements.txt
python tools/make_demo_db.py      # 生成 data/weibo.db，20 条假数据
python tools/make_theme_gif.py    # 重新生成主题切换动图（需 Chrome/Edge）
python run.py                     # 监听 127.0.0.1:5055
```

判断成功：控制台打印启动横幅，`curl http://127.0.0.1:5055/` 返回 200，
页面里能找到 `class="card"`。

## 目录约定

- `DATA_DIR`（默认 `<仓库>/data`）放 `weibo.db`、`emoji/`、`bg/`、`fonts.json`、`annotations/`；其中数据目录本身和 `emoji/`、`bg/`、`annotations/` 在导入时自动创建
- `DATA_ROOT` 是可选配置，指向爬虫归档目录，图片和视频直接从那里读，不再复制一份
- `static/` 是前端资源，Flask 通过 `static_folder` 显式指向
- 配置写在仓库根目录的 `config.py`（不存在时全部用默认值）。文件用 UTF-8 保存，带 BOM 也能读

## 代码地图

| 文件 | 职责 |
|---|---|
| `weibo_reader/paths.py` | 所有路径在这里决定，其它模块不自己拼路径 |
| `weibo_reader/core.py` | Flask app、配置读取、SQLite、文本与表情渲染、FTS5 |
| `weibo_reader/render.py` | `render_weibo()` 渲染单条微博，`render_fav_card()` 渲染收藏卡片 |
| `weibo_reader/views.py` | 年鉴 / 年度报告 / 图谱 / 那年今日 / 体检 / 合集 |
| `weibo_reader/routes.py` | 全部 `@app.route`：首页、图片、视频、导出、分享图、字体、标注备份 |

改 `render.py` 生成的 HTML 时，同步检查 `static/app.css` 里有没有对应类名。
样式改完不用清浏览器缓存，`_static_url()` 会在 URL 上拼 mtime 版本号。

## 数据表结构（最小集）

`user(id, nick_name, ...)`、`weibo(id, bid, user_id, screen_name, text, pics, created_at,
source, attitudes_count, retweet_id, ...)`、`comments(...)`、`reposts(...)`。
完整 DDL 见 `tools/make_demo_db.py` 里的 `SCHEMA`。

启动时 `ensure_columns()` 会给 `weibo` 表补两列（`location_url`、`region`），
并自动创建 `favorites`、`weibo_tags`、`weibo_fts` 以及同步触发器，不需要手工迁移。

## 常见错误

| 现象 | 原因 / 处理 |
|---|---|
| `ModuleNotFoundError: flask` | 没装依赖，跑 `pip install -r requirements.txt` |
| 页面空白、没有卡片 | `DATA_DIR` 里没有 `weibo.db`，先跑 `tools/make_demo_db.py` |
| 端口被占用 | 改 `config.py` 里的 `PORT` |
| `Failed to connect to github.com:443 over proxy 127.0.0.1` | git 配了代理但代理没启动。看 `git config --global --get http.proxy`，用 `git config --global --unset http.proxy` 和 `--unset https.proxy` 清掉，或先把代理软件打开 |
| 控制台中文乱码 | 终端编码不是 GBK / UTF-8，Windows 下用 `chcp 936` 或 `chcp 65001` |
| 图片全是“图片未下载” | `DATA_ROOT` 没配，或目录名与 `user.nick_name` 不一致 |
| 爬虫反复报 `Expecting value: line 1 column 1 (char 0)` | Cookie 过期。未登录时 `m.weibo.cn` 回的是 HTML 不是 JSON，所以 `response.json()` 抛这个错。请求 `https://m.weibo.cn/api/config` 验证：`data.login` 为 `false` 即过期，重新取 Cookie 填回 `config.json` |

## 不要做的事

- 不要提交 `data/`、`*.db`、`config.py`，里面是个人数据，已在 `.gitignore` 里
- 不要把 `emoji/` 里的表情图打包进仓库，属于新浪版权素材
- 不要挂到公网：没有账号体系，只有可选的局域网口令
