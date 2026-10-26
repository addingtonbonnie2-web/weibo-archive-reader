# -*- coding: utf-8 -*-
"""路由层：Flask 应用与全部 HTTP 接口。"""

import json
import os
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote
from flask import Response, jsonify, redirect, request, send_from_directory

from .paths import ANNOT_DIR, FONTS_JSON

from .core import (
    app,
    BASE_DIR,
    EMOJI_DIR,
    _fts_query,
    _lan_ip,
    data_root,
    ensure_favorites,
    ensure_tags,
    find_avatar,
    find_local_images,
    fmt_time,
    get_conf,
    get_db,
    get_default_user_id,
    get_users,
    html_escape,
    norm_md_links,
    user_folder,
)
from .render import (
    _mk_options,
    render_fav_card,
    render_index_html,
    render_weibo,
)
from .views import (
    _view_head,
    view_graph,
    view_health,
    view_onthisday,
    view_report,
    view_tags,
    view_yearbook,
)

@app.route("/")
def index():
    user_id = request.args.get("user", "").strip()
    page = max(1, int(request.args.get("page", 1) or 1))
    q = request.args.get("q", "").strip()
    d1 = request.args.get("d1", "").strip()
    d2 = request.args.get("d2", "").strip()
    ftype = request.args.get("type", "").strip()
    fav = request.args.get("fav", "").strip()
    view = request.args.get("view", "").strip()
    year = request.args.get("year", "").strip()
    month = request.args.get("month", "").strip()
    hour = request.args.get("hour", "").strip()
    wid = request.args.get("wid", "").strip()
    # 日期填反（起始>结束）时自动交换，避免永远搜不到
    if d1 and d2 and d1 > d2:
        d1, d2 = d2, d1
    users = get_users()
    if not users:
        return ("还没有备份数据。先运行 python tools/make_demo_db.py 看示例，"
            "或把自己的 weibo.db 放进 data 目录后再刷新"), 200

    if not user_id:
        user_id = get_default_user_id() or users[0][0]
    # 校验 user_id 存在
    ids = [u[0] for u in users]
    if user_id not in ids:
        user_id = users[0][0]
    nick = dict(users).get(user_id, user_id)

    users_map = dict(users)
    con = get_db()

    # ===== 续读跳转：?to=<created_at> 算出它在第几页再重定向 =====
    _to = request.args.get("to", "").strip()
    if _to and not view and not fav and not wid \
            and re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", _to):
        n_before = con.execute(
            "SELECT COUNT(*) FROM weibo WHERE user_id=? AND created_at > ?",
            (user_id, _to)).fetchone()[0]
        con.close()
        return redirect("/?user=%s&page=%d&hl=%s"
                        % (user_id, n_before // 20 + 1, quote(_to)))

    # ===== 功能视图分发：那年今日 / 年鉴 / 互动图谱 / 年度报告 =====
    if view in ("onthisday", "yearbook", "graph", "report", "health", "tags"):
        if view == "onthisday":
            return view_onthisday(user_id, nick, users, users_map, q)
        if view == "yearbook":
            return view_yearbook(user_id, nick, users, users_map, year, month, q, page)
        if view == "graph":
            return view_graph(user_id, nick, users, users_map)
        if view == "report":
            return view_report(user_id, nick, users, users_map, year, q)
        if view == "health":
            return view_health(user_id, nick, users, users_map, q)
        if view == "tags":
            return view_tags(user_id, nick, users, users_map)

    # ===== 单条视图：报告"最热微博"点击跳转 =====
    if wid:
        wrow = con.execute(
            "SELECT * FROM weibo WHERE id=?", (wid,)
        ).fetchone()
        if wrow:
            card = render_weibo(wrow, users_map, user_id, q)
            head = _view_head(f'📌 <b>单条微博</b>')
            options = _mk_options(users, user_id)
            body = (f'<div style="max-width:720px;margin:0 auto">{card}</div>'
                    f'<div style="text-align:center;margin:16px 0">'
                    f'<a class="btn" href="/?user={user_id}">← 返回时间线</a></div>')
            return render_index_html(nick, user_id, 0, body, options, "", "", "", "", f"user={user_id}&view=single&wid={wid}", 1, 1, "", False, view="single", view_head=head, cnt_label="单条微博")
        return f'<div class="empty">找不到该微博（wid={html_escape(wid)}）</div>'

    # ===== 收藏模式 =====
    if fav:
        fwhere = ["owner_uid=?"]
        fargs = [user_id]
        if q:
            fwhere.append("text LIKE ?")
            fargs.append("%" + q + "%")
        fsql = " AND ".join(fwhere)
        try:
            frows = con.execute(
                f"SELECT * FROM favorites WHERE {fsql} ORDER BY id DESC", fargs
            ).fetchall()
        except sqlite3.OperationalError:
            # 表不存在（老库）：补建后按空收藏夹处理，不再 500
            con.close()
            ensure_favorites()
            con = get_db()
            frows = []
        con.close()
        total = len(frows)
        # 按收藏标签分组：有标签的按标签名，没标签的归到「未分类」
        groups = {}
        for r in frows:
            try:
                t = (r["tag"] or "").strip()
            except Exception:
                t = ""
            groups.setdefault(t, []).append(r)
        tagged = sorted([g for g in groups if g], key=lambda k: -len(groups[k]))
        order = tagged + ([""] if "" in groups else [])
        if len(order) > 1:
            parts = []
            for g in order:
                rows_g = groups[g]
                title = f"📁 {html_escape(g)}" if g else "📂 未分类"
                parts.append(
                    f'<div class="fav-tag">{title}'
                    f'<span class="fav-tag-n">{len(rows_g)}</span></div>'
                    + "".join(render_fav_card(r) for r in rows_g))
            cards = "".join(parts)
        else:
            cards = "".join(render_fav_card(r) for r in frows)
        cards = cards or ('<div class="empty">收藏夹是空的。在微博里点过收藏后，'
                      '用抓取脚本重新备份一次，这里就会出现。</div>')
        # 收藏页不需要分页/日期筛选，参数重建
        qs = f"user={user_id}&fav=1"
        page_count = 1
        pager = ""
        q_esc = html_escape(q)
        d1 = d2 = ""
        ftype = ""
        options = ""
        for uid, n in users:
            sel = " selected" if uid == user_id else ""
            options += f'<option value="{uid}"{sel}>{html_escape(n)}（{uid}）</option>'
        return render_index_html(nick, user_id, total, cards, options, q_esc, d1, d2, ftype, qs, page, page_count, pager, fav=True)

    # ===== 微博列表模式 =====
    # 动态筛选：关键词 + 日期范围
    where = ["user_id=?"]
    args = [user_id]
    if q:
        # 关键词匹配：微博正文 + （转发时）原帖正文
        # 3 字以上走 FTS5（trigram 子串），1-2 字 trigram 不支持，退回 LIKE
        if _FTS_OK and len(q) >= 3:
            where.append("(id IN (SELECT id FROM weibo_fts WHERE weibo_fts MATCH ?) "
                         "OR retweet_id IN (SELECT id FROM weibo_fts WHERE weibo_fts MATCH ?))")
            args += [_fts_query(q), _fts_query(q)]
        else:
            where.append("(text LIKE ? OR EXISTS (SELECT 1 FROM weibo o "
                         "WHERE o.id=weibo.retweet_id AND o.text LIKE ?))")
            args += ["%" + q + "%", "%" + q + "%"]
    if d1:
        where.append("date(created_at) >= ?")
        args.append(d1)
    if d2:
        where.append("date(created_at) <= ?")
        args.append(d2)
    # 时段（小时）筛选：报告"发博时段分布"点击跳转用
    if hour:
        where.append("substr(created_at,12,2)=?")
        args.append(hour)
    # 类型筛选：原创 / 转发 / 文章 / 有获赞 / 有评论 / 有转发互动
    if ftype == "orig":
        where.append("(retweet_id IS NULL OR retweet_id='')")
    elif ftype == "retweet":
        where.append("(retweet_id IS NOT NULL AND retweet_id!='')")
    elif ftype == "article":
        where.append("(article_url IS NOT NULL AND article_url!='')")
    elif ftype == "liked":
        where.append("(attitudes_count IS NOT NULL AND attitudes_count > 0)")
    elif ftype == "commented":
        where.append("(comments_count IS NOT NULL AND comments_count > 0)")
    elif ftype == "reposted":
        where.append("(reposts_count IS NOT NULL AND reposts_count > 0)")
    # 标签筛选（本地自定义标注）
    tag = request.args.get("tag", "").strip()
    if tag:
        where.append("id IN (SELECT weibo_id FROM weibo_tags WHERE tag=?)")
        args.append(tag)
    where_sql = " AND ".join(where)
    total = con.execute(
        f"SELECT COUNT(*) FROM weibo WHERE {where_sql}", args
    ).fetchone()[0]
    rows = con.execute(
        f"SELECT * FROM weibo WHERE {where_sql} ORDER BY created_at DESC LIMIT 20 OFFSET ?",
        args + [(page - 1) * 20],
    ).fetchall()
    con.close()

    # 账号下拉选项
    options = ""
    for uid, n in users:
        sel = " selected" if uid == user_id else ""
        options += f'<option value="{uid}"{sel}>{html_escape(n)}（{uid}）</option>'

    cards = "".join(
        render_weibo(r, users_map, user_id, q) for r in rows
    ) or '<div class="empty">没有符合条件的微博（换个关键词或日期试试）</div>'

    # 分页（保留筛选参数）
    qs = f"user={user_id}"
    if q:
        qs += "&q=" + quote(q)
    if d1:
        qs += f"&d1={d1}"
    if d2:
        qs += f"&d2={d2}"
    if ftype:
        qs += f"&type={ftype}"
    if hour:
        qs += f"&hour={hour}"
    if tag:
        qs += "&tag=" + quote(tag)
    # 搜索框回填值（HTML 转义）
    q_esc = html_escape(q)
    page_count = max(1, (total + 19) // 20)
    pager = ""
    if page_count > 1:
        prev_dis = 'style="pointer-events:none;opacity:.4"' if page <= 1 else ""
        nxt_dis = 'style="pointer-events:none;opacity:.4"' if page >= page_count else ""
        pager = (
            f'<div class="pager">'
            f'<a href="/?{qs}&page={page-1}" {prev_dis}>← 上一页</a>'
            f'<span>{page} / {page_count}（共 {total} 条）</span>'
            f'<a href="/?{qs}&page={page+1}" {nxt_dis}>下一页 →</a>'
            f'</div>'
        )

    return render_index_html(nick, user_id, total, cards, options, q_esc, d1, d2, ftype, qs, page, page_count, pager, fav)

@app.route("/fav_img/<path:filename>")
def serve_fav_img(filename):
    """服务收藏图片 fav_img/ 目录"""
    fav_dir = os.path.join(BASE_DIR, "fav_img")
    if os.path.isfile(os.path.join(fav_dir, filename)):
        return send_from_directory(fav_dir, filename)
    return "", 404

@app.route("/img/<path:filename>")
def serve_img(filename):
    """服务本地图片：先查收藏图，再查数据根目录下的各用户文件夹 img/"""
    # 收藏图片目录（根目录 fav_img）
    fav_dir = os.path.join(BASE_DIR, "fav_img")
    if os.path.isfile(os.path.join(fav_dir, filename)):
        return send_from_directory(fav_dir, filename)
    roots = [data_root()]
    if roots[0] != BASE_DIR:
        roots.append(BASE_DIR)
    for root in roots:
        try:
            names = os.listdir(root)
        except Exception:
            continue
        for name in names:
            p = os.path.join(root, name)
            if os.path.isdir(p):
                img_dir = os.path.join(p, "img")
                if os.path.isdir(img_dir):
                    target = os.path.join(img_dir, filename)
                    if os.path.isfile(target):
                        return send_from_directory(img_dir, filename)
    return "", 404

@app.route("/video/<path:filename>")
def serve_video(filename):
    """服务本地视频：查数据根目录下各账号文件夹的 video/（支持拖动进度条）"""
    roots = [data_root()]
    if roots[0] != BASE_DIR:
        roots.append(BASE_DIR)
    for root in roots:
        try:
            names = os.listdir(root)
        except Exception:
            continue
        for name in names:
            p = os.path.join(root, name)
            if os.path.isdir(p):
                vdir = os.path.join(p, "video")
                if os.path.isdir(vdir) and os.path.isfile(os.path.join(vdir, filename)):
                    return send_from_directory(vdir, filename, conditional=True)
    return "", 404

@app.route("/avatar/<user_id>")
def serve_avatar(user_id):
    av = find_avatar(user_id)
    if av:
        return send_from_directory(os.path.dirname(av), os.path.basename(av))
    return "", 404


@app.route("/api/upload_bg", methods=["POST"])
def upload_bg():
    """接收用户上传的背景图片，保存到 bg/ 目录，返回可访问 URL"""
    import uuid
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "未收到文件"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        return jsonify({"error": "不支持的图片格式"}), 400
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > 10 * 1024 * 1024:
        return jsonify({"error": "图片超过 10MB"}), 400
    os.makedirs(BG_DIR, exist_ok=True)
    name = uuid.uuid4().hex[:12] + ext
    f.save(os.path.join(BG_DIR, name))
    return jsonify({"url": f"/bg/{name}"})

@app.route("/bg/<path:filename>")
def serve_bg(filename):
    return send_from_directory(BG_DIR, filename)

@app.route("/emoji/<path:filename>")
def serve_emoji(filename):
    return send_from_directory(EMOJI_DIR, filename)

@app.route("/api/users")
def api_users():
    return jsonify([{"id": u, "nick": n} for u, n in get_users()])

@app.route("/api/comments")
def api_comments():
    """返回某条微博的全部本地评论（按热度排序）"""
    wid = request.args.get("weibo_id", "").strip()
    if not wid:
        return jsonify({"error": "缺少 weibo_id"}), 400
    con = get_db()
    rows = con.execute(
        "SELECT user_screen_name, user_avatar_url, text, like_count, created_at, ip_location "
        "FROM comments WHERE weibo_id=? ORDER BY like_count DESC",
        (wid,),
    ).fetchall()
    con.close()
    return jsonify([{
        "user": r["user_screen_name"] or "网友",
        "avatar": r["user_avatar_url"] or "",
        "text": r["text"] or "",
        "likes": r["like_count"] or 0,
        "time": fmt_time(r["created_at"]),
        "ip": (r["ip_location"] or "").strip(),
    } for r in rows])

# ===== 全文检索（FTS5 + trigram，支持中文子串）=====
_FTS_OK = False

# ===== 自定义标签（本地标注，不联网）=====

@app.route("/api/tag", methods=["POST"])
def api_tag():
    wid = (request.form.get("wid") or "").strip()
    tag = (request.form.get("tag") or "").strip()[:30]
    act = (request.form.get("act") or "add").strip()
    if not wid or not tag:
        return jsonify(ok=False, msg="缺少参数"), 400
    try:
        con = get_db()
        if act == "del":
            con.execute("DELETE FROM weibo_tags WHERE weibo_id=? AND tag=?", (wid, tag))
        else:
            exists = con.execute("SELECT 1 FROM weibo_tags WHERE weibo_id=? AND tag=?",
                                 (wid, tag)).fetchone()
            if not exists:
                con.execute("INSERT INTO weibo_tags(weibo_id, tag, created_at) VALUES (?,?,?)",
                            (wid, tag, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
        con.close()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, msg=str(e)), 500


ensure_tags()

@app.route("/export.md")
def export_md():
    """把当前筛选结果导出成 Markdown（图片用本地绝对路径，Typora/Obsidian 能直接显示）"""
    user_id = request.args.get("user", "").strip()
    q = request.args.get("q", "").strip()
    d1 = request.args.get("d1", "").strip()
    d2 = request.args.get("d2", "").strip()
    ftype = request.args.get("type", "").strip()
    year = request.args.get("year", "").strip()
    try:
        limit = max(1, min(int(request.args.get("limit", "2000") or 2000), 20000))
    except Exception:
        limit = 2000

    users = get_users()
    ids = [u[0] for u in users]
    if user_id not in ids:
        user_id = ids[0] if ids else ""
    nick = dict(users).get(user_id, user_id)

    con = get_db()
    where = ["user_id=?"]
    args = [user_id]
    if q:
        if _FTS_OK and len(q) >= 3:
            where.append("(id IN (SELECT id FROM weibo_fts WHERE weibo_fts MATCH ?) "
                         "OR retweet_id IN (SELECT id FROM weibo_fts WHERE weibo_fts MATCH ?))")
            args += [_fts_query(q), _fts_query(q)]
        else:
            where.append("(text LIKE ? OR EXISTS (SELECT 1 FROM weibo o "
                         "WHERE o.id=weibo.retweet_id AND o.text LIKE ?))")
            args += ["%" + q + "%", "%" + q + "%"]
    if year:
        where.append("substr(created_at,1,4)=?")
        args.append(year)
    if d1:
        where.append("date(created_at) >= ?")
        args.append(d1)
    if d2:
        where.append("date(created_at) <= ?")
        args.append(d2)
    if ftype == "orig":
        where.append("(retweet_id IS NULL OR retweet_id='')")
    elif ftype == "retweet":
        where.append("(retweet_id IS NOT NULL AND retweet_id!='')")
    elif ftype == "article":
        where.append("(article_url IS NOT NULL AND article_url!='')")
    elif ftype == "liked":
        where.append("(attitudes_count > 0)")
    elif ftype == "commented":
        where.append("(comments_count > 0)")
    elif ftype == "reposted":
        where.append("(reposts_count > 0)")
    wsql = " AND ".join(where)
    total = con.execute("SELECT COUNT(*) FROM weibo WHERE " + wsql, args).fetchone()[0]
    rows = con.execute("SELECT * FROM weibo WHERE " + wsql +
                       " ORDER BY created_at DESC LIMIT ?", args + [limit]).fetchall()
    con.close()

    # 图片目录建一次索引（时间戳前缀 -> 文件名列表），比逐条扫目录快几百倍
    folder = user_folder(user_id) or ""
    img_dir = os.path.join(folder, "img") if folder else ""
    idx = {}
    if img_dir and os.path.isdir(img_dir):
        for fn in os.listdir(img_dir):
            m = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})", fn)
            if m:
                idx.setdefault(m.group(1), []).append(fn)
        for k in idx:
            idx[k].sort()

    title_parts = []
    if year:
        title_parts.append(year + " 年")
    if d1 or d2:
        title_parts.append("%s ~ %s" % (d1 or "最早", d2 or "最新"))
    if q:
        title_parts.append("关键词「%s」" % q)
    typemap = {"orig": "原创", "retweet": "转发", "article": "文章", "liked": "有获赞",
               "commented": "有评论", "reposted": "有转发互动"}
    if ftype in typemap:
        title_parts.append(typemap[ftype])

    out = ["# %s · 微博导出" % nick, ""]
    out.append("- 账号：%s（%s）" % (nick, user_id))
    out.append("- 筛选：%s" % (" · ".join(title_parts) if title_parts else "全部"))
    out.append("- 命中：%d 条%s" % (total, "（导出前 %d 条）" % limit if total > len(rows) else ""))
    out.append("- 导出时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    out.append("")
    out.append("---")
    out.append("")

    for r in rows:
        ts = str(r["created_at"] or "")
        out.append("## %s" % ts)
        out.append("")
        text = norm_md_links(str(r["text"] or "")).strip()
        if text:
            out.append(text)
            out.append("")
        try:
            rt = (r["retweet_text"] or "").strip()
        except Exception:
            rt = ""
        rid = str(r["retweet_id"] or "")
        if rid and not rt:
            out.append("> 转发原帖：https://m.weibo.cn/detail/%s" % rid)
        if rt:
            out.append("> **转发原文**")
            for line in re.sub(r"^\s*转发[:：]\s*", "", rt).splitlines():
                out.append("> " + line if line.strip() else ">")
        if out and out[-1] != "":
            out.append("")
        prefix = ts.replace(" ", "_").replace(":", "-")
        for fn in idx.get(prefix, []):
            out.append("![img](%s)" % os.path.join(img_dir, fn).replace("\\", "/"))
        if idx.get(prefix):
            out.append("")
        src = str(r["source"] or "").strip()
        extra = " · ".join([x for x in (
            ("来自 " + src) if src else "",
            ("赞 %s" % r["attitudes_count"]) if r["attitudes_count"] else "",
            ("评论 %s" % r["comments_count"]) if r["comments_count"] else "",
            ("转发 %s" % r["reposts_count"]) if r["reposts_count"] else "",
            "原帖 https://m.weibo.cn/detail/%s" % r["id"],
        ) if x])
        out.append("<sub>%s</sub>" % extra)
        out.append("")
        out.append("---")
        out.append("")

    body = "\n".join(out)
    fname = "weibo-%s-%s.md" % (user_id, datetime.now().strftime("%Y%m%d-%H%M"))
    return Response(body, mimetype="text/markdown",
                    headers={"Content-Disposition": "attachment; filename=%s" % fname})

# ===== 分享图：把单条微博画成一张 1080 宽的 PNG =====
_FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

_FONT_REG = r"C:\Windows\Fonts\msyh.ttc"

def _font(size, bold=False):
    from PIL import ImageFont
    for p in ((_FONT_BOLD, _FONT_REG) if bold else (_FONT_REG, _FONT_BOLD)):
        try:
            if os.path.isfile(p):
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    return None

def _wrap(draw, text, font, max_w, max_lines=0):
    """按像素宽度折行（中文逐字，英文按词）"""
    lines, cur = [], ""
    for ch in str(text):
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        try:
            w = draw.textlength(trial, font=font)
        except Exception:
            w = len(trial) * 12
        if w > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1][: max(0, len(lines[-1]) - 1)] + "…"
    return lines

@app.route("/share/<wid>.png")
def share_png(wid):
    """单条微博 -> 分享图（1080 宽，白底红顶）"""
    from io import BytesIO
    from PIL import Image, ImageDraw

    con = get_db()
    w = con.execute("SELECT * FROM weibo WHERE id=?", (str(wid),)).fetchone()
    con.close()
    if not w:
        return "", 404

    W = 1080
    PAD = 56
    nick = str(w["screen_name"] or "")
    ts = str(w["created_at"] or "")[:16]
    src = str(w["source"] or "").strip()
    body = norm_md_links(str(w["text"] or "")).strip()

    f_nick, f_meta, f_body, f_tag = _font(40, True), _font(26), _font(34), _font(24)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    body_lines = _wrap(probe, body, f_body, W - PAD * 2, max_lines=18)
    line_h = 52
    top_h = 252
    body_h = len(body_lines) * line_h
    images = find_local_images(str(w["user_id"]), str(w["created_at"]))[:3]
    img_h = 0
    if images:
        img_h = 420 if len(images) > 1 else 520
    H = top_h + body_h + img_h + 150

    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=(230, 22, 45))

    # 头像
    ax, ay, ar = PAD, 60, 72
    folder = user_folder(str(w["user_id"])) or ""
    av_path = os.path.join(folder, "avatar.jpg") if folder else ""
    drew = False
    if av_path and os.path.isfile(av_path):
        try:
            av = Image.open(av_path).convert("RGB").resize((ar * 2, ar * 2))
            mask = Image.new("L", (ar * 2, ar * 2), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, ar * 2, ar * 2), fill=255)
            img.paste(av, (ax, ay), mask)
            drew = True
        except Exception:
            drew = False
    if not drew:
        d.ellipse([ax, ay, ax + ar * 2, ay + ar * 2], fill=(230, 22, 45))
        ch = (nick or "微")[0:1]
        try:
            tw = d.textlength(ch, font=f_nick)
            d.text((ax + ar - tw / 2, ay + ar - 28), ch, font=f_nick, fill="white")
        except Exception:
            pass

    d.text((ax + ar * 2 + 24, ay + 8), nick, font=f_nick, fill=(30, 33, 38))
    meta = ts + ((" · " + src) if src else "")
    d.text((ax + ar * 2 + 26, ay + 68), meta, font=f_meta, fill=(150, 155, 165))

    y = top_h
    for ln in body_lines:
        d.text((PAD, y), ln, font=f_body, fill=(40, 44, 52))
        y += line_h

    # 图片
    if images:
        folder_img = os.path.join(folder, "img") if folder else ""
        n = len(images)
        gap = 12
        cell = (W - PAD * 2 - gap * (n - 1)) // n
        for i, fn in enumerate(images):
            p = os.path.join(folder_img, fn)
            try:
                im = Image.open(p).convert("RGB")
                im.thumbnail((cell, img_h))
                x = PAD + i * (cell + gap)
                img.paste(im, (x, y + 16))
            except Exception:
                pass

    foot = "本地微博归档 · %s" % (ts[:10])
    d.text((PAD, H - 70), foot, font=f_tag, fill=(160, 165, 175))
    d.line([PAD, H - 90, W - PAD, H - 90], fill=(235, 237, 240), width=2)

    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0)
    return Response(buf.read(), mimetype="image/png",
                    headers={"Cache-Control": "no-store"})

# ===== 标注自动备份：油猴脚本（weibo.com）POST 过来 =====

@app.route("/api/annot", methods=["POST", "OPTIONS"])
def api_annot():
    """跨域接收标注 JSON，落盘到 DATA_DIR/annotations/"""
    origin = request.headers.get("Origin", "*")
    if request.method == "OPTIONS":
        resp = Response("", 204)
    else:
        data = request.get_json(force=True, silent=True) or {}
        ann = data.get("annotations") or {}
        try:
            os.makedirs(ANNOT_DIR, exist_ok=True)
            now = datetime.now()
            payload = {
                "saved_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(ann),
                "client_ts": data.get("ts", ""),
                "annotations": ann,
            }
            blob = json.dumps(payload, ensure_ascii=False, indent=1)
            with open(os.path.join(ANNOT_DIR, "annot-latest.json"), "w",
                      encoding="utf-8") as f:
                f.write(blob)
            with open(os.path.join(ANNOT_DIR, "annot-%s.json" % now.strftime("%Y%m%d-%H%M%S")),
                      "w", encoding="utf-8") as f:
                f.write(blob)
            # 只保留最近 50 份快照
            snaps = sorted(f for f in os.listdir(ANNOT_DIR)
                           if f.startswith("annot-2") and f.endswith(".json"))
            for old in snaps[:-50]:
                try:
                    os.remove(os.path.join(ANNOT_DIR, old))
                except Exception:
                    pass
            resp = Response(json.dumps({"ok": 1, "count": len(ann)}, ensure_ascii=False),
                            mimetype="application/json")
        except Exception as e:
            resp = Response(json.dumps({"ok": 0, "error": str(e)}, ensure_ascii=False),
                            status=500, mimetype="application/json")
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Private-Network"] = "true"
    resp.headers["Vary"] = "Origin"
    resp.headers["Cache-Control"] = "no-store"
    return resp

# ===== 本机字体列表（给设置面板做选择器）=====
@app.route("/api/fonts")
def api_fonts():
    """扫描 Windows 字体目录，返回 [{family, file, style}]，结果按目录 mtime 缓存"""
    cache = FONTS_JSON
    dirs = []
    win = os.environ.get("WINDIR", r"C:\Windows")
    dirs.append(os.path.join(win, "Fonts"))
    la = os.environ.get("LOCALAPPDATA")
    if la:
        dirs.append(os.path.join(la, "Microsoft", "Windows", "Fonts"))
    try:
        stamp = max(os.path.getmtime(d) for d in dirs if os.path.isdir(d)) if dirs else 0
    except Exception:
        stamp = 0
    try:
        if os.path.isfile(cache) and os.path.getmtime(cache) >= stamp:
            return Response(open(cache, encoding="utf-8").read(),
                            mimetype="application/json")
    except Exception:
        pass

    # 注册表里的「显示名」——Windows 其它软件里看到的名字（通常是中文名）
    disp = {}
    try:
        import winreg
        for root, flag in ((winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ),
                           (winreg.HKEY_CURRENT_USER, winreg.KEY_READ)):
            try:
                k = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                                   0, flag)
            except OSError:
                continue
            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(k, i)
                except OSError:
                    break
                i += 1
                base = os.path.basename(str(val)).lower()
                disp[base] = (name.replace(" (TrueType)", "").replace(" (OpenType)", "")
                              .replace(" (TrueType)", "").strip())
            winreg.CloseKey(k)
    except Exception:
        pass

    from PIL import ImageFont
    seen, out = set(), []
    exts = (".ttf", ".ttc", ".otf")
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(exts):
                continue
            p = os.path.join(d, fn)
            idxs = range(0, 8) if fn.lower().endswith(".ttc") else (0,)
            for idx in idxs:
                try:
                    fam, style = ImageFont.truetype(p, 16, index=idx).getname()
                except Exception:
                    continue
                if not fam or (fam, style) in seen:
                    continue
                seen.add((fam, style))
                out.append({"family": fam, "style": style or "", "file": fn,
                            "display": disp.get(fn.lower(), "")})
    out.sort(key=lambda x: x["family"].lower())
    blob = json.dumps({"count": len(out), "fonts": out}, ensure_ascii=False)
    try:
        with open(cache, "w", encoding="utf-8") as f:
            f.write(blob)
    except Exception:
        pass
    return Response(blob, mimetype="application/json")

if __name__ == "__main__":
    _host = get_conf("HOST", "127.0.0.1") or "127.0.0.1"
    try:
        _port = int(get_conf("PORT", "5055") or 5055)
    except Exception:
        _port = 5055
    print("=" * 52)
    print("  微博归档阅读器")
    print("  本机      : http://127.0.0.1:%d" % _port)
    if _host == "0.0.0.0":
        _ip = _lan_ip()
        if _ip:
            print("  手机/平板 : http://%s:%d   （同一 WiFi）" % (_ip, _port))
        print("  口令      : %s" % ("已设置（本机免口令）" if get_conf("ACCESS_CODE", "")
                                    else "未设置，同一 WiFi 的任何设备都能看"))
        print("  提示      : 首次可能弹 Windows 防火墙，选「专用网络」允许")
    else:
        print("  （当前只监听本机；想让手机访问，把 config.py 的 HOST 改成 0.0.0.0）")
    print("=" * 52)
    app.run(host=_host, port=_port, debug=False, threaded=True)
