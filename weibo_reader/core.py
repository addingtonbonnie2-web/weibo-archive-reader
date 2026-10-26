# -*- coding: utf-8 -*-
"""核心层：配置、路径、数据库、文本与表情渲染。

不依赖同包其它模块，可被任意引用。"""

import os
import re
import socket
import sqlite3
from datetime import datetime
from .paths import CONFIG_PY, DATA_DIR, DB_PATH, EMOJI_DIR, STATIC_DIR
from flask import Flask, redirect, request



# 数据目录（库 / 表情 / 背景图 / 字体缓存都在这里），由 paths.py 决定
BASE_DIR = DATA_DIR

IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")

def _static_url(name):
    """静态资源 URL（带 mtime 版本号，改完刷新就生效，不用清浏览器缓存）"""
    p = os.path.join(STATIC_DIR, name)
    try:
        return "/static/%s?v=%d" % (name, int(os.path.getmtime(p)))
    except Exception:
        return "/static/%s" % name

STATIC_CSS = _static_url("app.css")

STATIC_JS = _static_url("app.js")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")

def get_default_user_id():
    """读取 config.py 的 PRIVATE_USER_NAME，转换为 user_id；失败返回 None"""
    nick = None
    try:
        with open(CONFIG_PY, "r", encoding="utf-8-sig") as f:
            for line in f:
                if "PRIVATE_USER_NAME" in line and "=" in line:
                    nick = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass
    if nick:
        try:
            con = get_db()
            row = con.execute(
                "SELECT id FROM user WHERE nick_name=?", (nick,)
            ).fetchone()
            con.close()
            if row:
                return str(row[0])
        except Exception:
            pass
    return None

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# 收藏表：以前整库覆盖同步时被冲掉过，启动时自动补建（空表不报错）
FAVORITES_DDL = """
CREATE TABLE IF NOT EXISTS favorites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_uid   varchar(20),
  author_nick varchar(50),
  author_uid  varchar(20),
  weibo_id    varchar(20),
  time        varchar(30),
  text        TEXT,
  imgs        TEXT
)
"""

def ensure_favorites():
    """确保 favorites 表存在（缺表时「收藏」页会 500），并补 tag 列"""
    try:
        con = get_db()
        con.execute(FAVORITES_DDL)
        cols = [r[1] for r in con.execute("PRAGMA table_info(favorites)")]
        if "tag" not in cols:
            con.execute("ALTER TABLE favorites ADD COLUMN tag varchar(50) DEFAULT ''")
        con.commit()
        con.close()
        return True
    except Exception:
        return False

def get_users():
    """从 user 表取全部主账号"""
    con = get_db()
    rows = con.execute(
        "SELECT id, nick_name FROM user ORDER BY id"
    ).fetchall()
    con.close()
    return [(str(r["id"]), r["nick_name"]) for r in rows]

def get_conf(key, default=""):
    """读 config.py 里的一个配置项（KEY = "value" 或 KEY = 123）"""
    try:
        with open(CONFIG_PY, "r", encoding="utf-8-sig") as f:
            for line in f:
                s = line.strip()
                if s.startswith(key) and "=" in s and not s.startswith("#"):
                    v = s.split("=", 1)[1].strip()
                    if v[:1] in ("r", "R") and len(v) > 1 and v[1] in ('"', "'"):
                        v = v[1:].strip()
                    return v.strip('"').strip("'")
    except Exception:
        pass
    return default

def data_root():
    """图片/视频数据根目录。
    config.py 里配了 DATA_ROOT 就直接读备份区（MyWeiboArchive），
    不再往阅读器目录复制一份；没配就用阅读器自身目录。
    """
    v = get_conf("DATA_ROOT", "")
    return v if v and os.path.isdir(v) else BASE_DIR

# ===== 局域网访问口令（手机/平板）=====
def _is_local_client():
    return request.remote_addr in ("127.0.0.1", "::1")

def _login_page(next_url):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>微博归档阅读器 · 需要口令</title>
<style>
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#f6f7fb;
  display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
.box{{background:#fff;padding:30px 34px;border-radius:16px;text-align:center;
  box-shadow:0 10px 34px rgba(0,0,0,.09);border:1px solid rgba(0,0,0,.05)}}
h1{{font-size:17px;margin:0 0 8px;color:#222}}
p{{font-size:13px;color:#8a8f99;margin:0 0 18px}}
input[type=password]{{width:190px;padding:10px 12px;border:1px solid #dcdde2;border-radius:9px;
  font-size:16px;text-align:center;outline:none}}
input[type=password]:focus{{border-color:#e6162d}}
button{{margin-top:14px;width:100%;padding:10px 0;border:0;border-radius:9px;background:#e6162d;
  color:#fff;font-size:15px;cursor:pointer}}
button:hover{{background:#c91226}}
</style></head><body>
<form class="box" method="get" action="/__auth">
  <h1>微博归档阅读器</h1>
  <p>你正在从其它设备访问，请输入访问口令</p>
  <input type="hidden" name="next" value="{html_escape(next_url)}">
  <input type="password" name="code" placeholder="访问口令" autofocus>
  <button type="submit">进入</button>
</form></body></html>"""

@app.before_request
def _lan_guard():
    """非本机访问要口令（config.py 里 ACCESS_CODE 留空则完全不校验）"""
    code = get_conf("ACCESS_CODE", "")
    if not code or _is_local_client():
        return None
    p = request.path
    if p in ("/__auth", "/manifest.json", "/favicon.ico") or p.startswith("/static/"):
        return None
    if request.cookies.get("wb_access") == code:
        return None
    return _login_page(request.full_path), 401

@app.route("/__auth")
def _auth():
    code = get_conf("ACCESS_CODE", "")
    got = request.args.get("code", "")
    nxt = request.args.get("next") or "/"
    if not nxt.startswith("/") or nxt.startswith("//"):
        nxt = "/"
    if code and got == code:
        resp = redirect(nxt)
        resp.set_cookie("wb_access", got, max_age=86400 * 365, samesite="Lax")
        return resp
    return _login_page(nxt), 403

def user_folder(user_id):
    """按 user_id 找用户文件夹（目录名可能是昵称或UID）"""
    for root in (data_root(), BASE_DIR):
        try:
            names = os.listdir(root)
        except Exception:
            continue
        for name in names:
            p = os.path.join(root, name)
            if name == user_id and os.path.isdir(p):
                return p
    # 通过 user 表昵称匹配
    con = get_db()
    row = con.execute(
        "SELECT nick_name FROM user WHERE id=?", (user_id,)
    ).fetchone()
    con.close()
    if row:
        for root in (data_root(), BASE_DIR):
            p = os.path.join(root, row["nick_name"])
            if os.path.isdir(p):
                return p
    return None

def find_avatar(user_id):
    """找本地头像文件（用户文件夹/avatar.*）"""
    folder = user_folder(user_id)
    if not folder:
        return None
    for f in os.listdir(folder):
        if f.lower().startswith("avatar") and f.lower().endswith(IMG_EXTS):
            return os.path.join(folder, f)
    return None

def find_local_images(user_id, created_at):
    """按微博发布时间找本地图片文件列表：
    img/{YYYY-MM-DD_HH-MM-SS}_{n}.{ext}
    返回相对 img 目录的文件名列表（按序号排序）
    """
    folder = user_folder(user_id)
    if not folder:
        return []
    img_dir = os.path.join(folder, "img")
    if not os.path.isdir(img_dir):
        return []
    try:
        t = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        prefix = t.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        return []
    matches = []
    for f in os.listdir(img_dir):
        # 单图: 2022-10-19_16-26-47.jpg；多图: 2022-10-19_16-26-47_1.jpg
        if (f.startswith(prefix + "_") or f.startswith(prefix + ".")) and f.lower().endswith(IMG_EXTS):
            matches.append(f)
    def _pic_no(f):
        m = re.search(r"_(\d+)\.", f)
        return int(m.group(1)) if m else 0
    matches.sort(key=_pic_no)
    return matches

def find_local_video(user_id, created_at):
    """按微博发布时间找本地视频：video/{YYYY-MM-DD_HH-MM-SS}.mp4"""
    folder = user_folder(user_id)
    if not folder:
        return ""
    vdir = os.path.join(folder, "video")
    if not os.path.isdir(vdir):
        return ""
    try:
        t = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        prefix = t.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        return ""
    for f in os.listdir(vdir):
        if f.startswith(prefix) and f.lower().endswith((".mp4", ".m4v", ".webm")):
            return f
    return ""

def html_escape(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_EMOJI_FILES = None

def get_emoji_files():
    """返回本地已有表情映射 {名字: 扩展名}，用于 [xx] -> 表情图渲染"""
    global _EMOJI_FILES
    if _EMOJI_FILES is None:
        _EMOJI_FILES = {}
        if os.path.isdir(EMOJI_DIR):
            for f in os.listdir(EMOJI_DIR):
                name, ext = os.path.splitext(f)
                if ext.lower() in (".png", ".gif", ".jpg"):
                    _EMOJI_FILES[name] = ext.lower()
    return _EMOJI_FILES

def render_emoji(html_text):
    """把已转义文本中的 [表情名] 替换成本地表情图 <img>（无图则保留原文字）"""
    if not html_text or "[" not in html_text:
        return html_text
    files = get_emoji_files()
    if not files:
        return html_text

    def _rep(m):
        name = m.group(1)
        ext = files.get(name)
        if ext:
            return (
                f'<img class="wb-emoji" src="/emoji/{name}{ext}" '
                f'title="[{name}]" alt="[{name}]" loading="lazy">'
            )
        return m.group(0)

    # 名字里可能带 → _ ~ 等符号（如 →_→），长度也放宽到 14
    return re.sub("\\[([\u4e00-\u9fa5A-Za-z0-9\\u2192_~-]{1,14})\\]", _rep, html_text)

def fmt_time(s):
    """微博时间统一显示 YYYY-MM-DD HH:MM:SS（兼容英文原始格式与ISO格式）"""
    if not s:
        return ""
    s = str(s).strip()
    try:
        return datetime.strptime(
            s, "%a %b %d %H:%M:%S %z %Y"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.strptime(
                s, "%Y-%m-%d %H:%M:%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return s[:19] if len(s) >= 19 else s

def norm_md_links(text):
    """把 markdown 链接 [文字](url) 转成「文字 url」
    （从 .md 恢复的历史微博，正文里保留着 md 的链接语法）"""
    if not text:
        return text or ""
    if "](" not in text:
        return text
    return re.sub(r"\[([^\]\n]{0,40})\]\((https?://[^)\s]+)\)", r"\1 \2", text)

def fmt_text(text, hl=""):
    """正文转HTML：转义 + 换行 + 话题/@ 简单高亮 + 超话钻石图标

    hl：搜索关键词。命中的片段先插不可见的占位符，转义/换行/链接处理完之后
    再换成 <mark>，这样绝不会破坏已经生成的 HTML 标签。
    """
    if not text:
        return ""
    t = str(text)
    if hl:
        try:
            t = re.sub(re.escape(hl),
                       lambda m: "\x01" + m.group(0) + "\x02", t, flags=re.I)
        except Exception:
            pass
    t = html_escape(t)
    t = t.replace("\n", "<br>")
    t = re.sub(
        r"#([^#\n]+)#",
        r'<span style="color:var(--chart-c1)">#\1#</span>',
        t,
    )
    t = re.sub(
        r"@([\w\u4e00-\u9fa5\-]+)",
        r'<span style="color:#1b7ab9">@\1</span>',
        t,
    )
    # 超话（钻石图标 + 橙色）：识别 "xxx超话"（词体 1-24 字，前无文字/字母/数字）
    t = re.sub(
        r"(?<![\w\u4e00-\u9fa5])([\w\u4e00-\u9fa5·\-]{1,24}?)超话(?![\w\u4e00-\u9fa5])",
        r'<span class="chaohua"><svg class="ch-icon" viewBox="0 0 16 16" width="11" height="11" aria-hidden="true"><path d="M8 1.5 L13.5 8 L8 14.5 L2.5 8 Z" fill="#ff8200" opacity="0.9"/><path d="M8 4.5 L11 8 L8 11.5 L5 8 Z" fill="#ffd591"/></svg>\1超话</span>',
        t,
    )
    # 自动把 http(s):// URL 变成可点击链接
    t = re.sub(
        r"(https?://[^\s<\u4e00-\u9fa5]+)",
        r'<a href="\1" target="_blank" rel="noopener" style="color:#1b7ab9;text-decoration:underline">\1</a>',
        t,
    )
    if hl:
        t = t.replace("\x01", '<mark class="hl-kw">').replace("\x02", "</mark>")
    return render_emoji(t)

def ensure_columns():
    """补建老库可能缺的列（location_url 由 补抓原帖.py 写入）"""
    try:
        con = get_db()
        cols = [r[1] for r in con.execute("PRAGMA table_info(weibo)")]
        if "location_url" not in cols:
            con.execute("ALTER TABLE weibo ADD COLUMN location_url varchar(300) DEFAULT ''")
        if "region" not in cols:
            con.execute("ALTER TABLE weibo ADD COLUMN region varchar(50) DEFAULT ''")
        con.commit()
        con.close()
    except Exception:
        pass

def ensure_fts(rebuild=False):
    """建 weibo_fts 虚拟表 + 增删改触发器，并保证和 weibo 表条数对得上"""
    global _FTS_OK
    try:
        con = get_db()
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS weibo_fts "
                    "USING fts5(id UNINDEXED, text, tokenize='trigram')")
        for ddl in (
            "CREATE TRIGGER IF NOT EXISTS weibo_fts_ai AFTER INSERT ON weibo BEGIN "
            "INSERT INTO weibo_fts(id, text) VALUES (new.id, IFNULL(new.text,'')); END",
            "CREATE TRIGGER IF NOT EXISTS weibo_fts_ad AFTER DELETE ON weibo BEGIN "
            "DELETE FROM weibo_fts WHERE id = old.id; END",
            "CREATE TRIGGER IF NOT EXISTS weibo_fts_au AFTER UPDATE OF text ON weibo BEGIN "
            "DELETE FROM weibo_fts WHERE id = old.id; "
            "INSERT INTO weibo_fts(id, text) VALUES (new.id, IFNULL(new.text,'')); END",
        ):
            con.execute(ddl)
        n_fts = con.execute("SELECT COUNT(*) FROM weibo_fts").fetchone()[0]
        n_db = con.execute("SELECT COUNT(*) FROM weibo").fetchone()[0]
        if rebuild or n_fts < n_db:
            con.execute("DELETE FROM weibo_fts")
            con.execute("INSERT INTO weibo_fts(id, text) "
                        "SELECT id, IFNULL(text,'') FROM weibo")
            con.commit()
        con.close()
        _FTS_OK = True
    except Exception:
        _FTS_OK = False
    return _FTS_OK

def _fts_query(q):
    """转成 FTS5 短语查询（内部双引号转义）"""
    return '"' + str(q).replace('"', '""') + '"'



TAGS_DDL = """
CREATE TABLE IF NOT EXISTS weibo_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  weibo_id varchar(20),
  tag      varchar(50),
  created_at varchar(30)
)
"""


def ensure_tags():
    try:
        con = get_db()
        con.execute(TAGS_DDL)
        con.execute("CREATE INDEX IF NOT EXISTS idx_wtags_wid ON weibo_tags(weibo_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_wtags_tag ON weibo_tags(tag)")
        con.commit()
        con.close()
    except Exception as e:
        print("[init] ensure_tags 失败：%s" % e)

def tags_of(weibo_id):
    try:
        con = get_db()
        rows = [r[0] for r in con.execute(
            "SELECT tag FROM weibo_tags WHERE weibo_id=? ORDER BY tag", (str(weibo_id),))]
        con.close()
        return rows
    except Exception:
        return []

def _lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


def init_schema():
    """启动时补齐表 / 列 / 索引。

    顺序无所谓，但四个都要跑：
      favorites 缺表 -> 收藏页 500
      weibo_tags 缺表 -> 合集页 500
      location_url 缺列 -> 原帖链接相关功能异常
      weibo_fts 缺表 -> 搜索不可用
    """
    ensure_favorites()
    ensure_columns()
    ensure_fts()
    ensure_tags()


init_schema()
