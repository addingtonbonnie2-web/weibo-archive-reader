# -*- coding: utf-8 -*-
"""渲染层：把一条微博 / 一张卡片渲染成 HTML 片段。"""

import json
import re
from urllib.parse import quote

from .core import (
    STATIC_CSS,
    STATIC_JS,
    find_avatar,
    find_local_images,
    find_local_video,
    fmt_text,
    fmt_time,
    get_db,
    html_escape,
    norm_md_links,
    tags_of,
)

def render_weibo(w, users_map, cur_user_id, q=""):
    """渲染单条微博卡片 HTML"""
    uid = str(w["user_id"])
    nick = users_map.get(uid, w["screen_name"] or uid)
    created = str(w["created_at"])[:16] if w["created_at"] else ""

    # 头像：本地优先，远程兜底（远程可能403，onerror隐藏）
    avatar_local = find_avatar(uid)
    if avatar_local:
        avatar_html = (
            f'<img class="avatar" src="/avatar/{uid}" onerror="this.style.display=\'none\'">'
        )
    else:
        avatar_url = ""
        con = get_db()
        row = con.execute(
            "SELECT avatar_url FROM user WHERE id=?", (uid,)
        ).fetchone()
        con.close()
        if row:
            avatar_url = row["avatar_url"] or ""
        avatar_html = (
            f'<img class="avatar" src="{html_escape(avatar_url)}" '
            f'onerror="this.style.display=\'none\'">'
        )

    # 图片九宫格：本地优先
    local_imgs = find_local_images(cur_user_id, str(w["created_at"])) if w["created_at"] else []
    pics = []
    if w["pics"]:
        pics = [p.strip() for p in str(w["pics"]).split(",") if p.strip().startswith("http")]
    imgs_html = ""
    if local_imgs:
        cells = ""
        for fname in local_imgs:
            cells += f'<div class="ph"><img loading="lazy" src="/img/{fname}" onclick="wbLightbox(this)"></div>'
        imgs_html = f'<div class="pics {"p1" if len(local_imgs)==1 else ("p2" if len(local_imgs)==2 else "")}">{cells}</div>'
    elif pics:
        cells = ""
        for u in pics:
            cells += (
                f'<div class="ph"><img loading="lazy" src="{html_escape(u)}" '
                f'onerror="this.parentNode.style.display=\'none\'" '
                f'onclick="wbLightbox(this)"></div>'
            )
        imgs_html = f'<div class="pics {"p1" if len(pics)==1 else ("p2" if len(pics)==2 else "")}">{cells}</div>'

    # 转发：显示原帖内容块（作者+正文+图片，本地优先）
    orig_block = ""
    # 从 md 恢复的历史微博没有原帖 id，但库里存了转发原文（retweet_text）
    try:
        _rt_text = (w["retweet_text"] or "").strip()
    except Exception:
        _rt_text = ""
    if w["retweet_id"]:
        con = get_db()
        orig = con.execute(
            "SELECT text, screen_name, pics, created_at FROM weibo WHERE id=?",
            (str(w["retweet_id"]),),
        ).fetchone()
        con.close()
        if orig:
            o_created = str(orig["created_at"]) if orig["created_at"] else ""
            o_local = find_local_images(cur_user_id, o_created) if o_created else []
            o_vid = find_local_video(cur_user_id, o_created) if o_created else ""
            o_video_html = (
                f'<div class="wb-video"><video controls preload="metadata" playsinline '
                f'src="/video/{quote(o_vid)}"></video></div>'
            ) if o_vid else ""
            o_pics = [
                p.strip()
                for p in str(orig["pics"] or "").split(",")
                if p.strip().startswith("http")
            ]
            o_cells = ""
            if o_local:
                for fname in o_local:
                    o_cells += f'<div class="ph"><img loading="lazy" src="/img/{fname}" onclick="wbLightbox(this)"></div>'
                o_n = len(o_local)
            elif o_pics:
                for u in o_pics:
                    o_cells += (
                        f'<div class="ph"><img loading="lazy" src="{html_escape(u)}" '
                        f'onerror="this.parentNode.style.display=\'none\'" '
                        f'onclick="wbLightbox(this)"></div>'
                    )
                o_n = len(o_pics)
            else:
                o_cells, o_n = "", 0
            orig_imgs_html = (
                f'<div class="pics {"p1" if o_n==1 else ("p2" if o_n==2 else "")}">{o_cells}</div>' if o_cells else ""
            )
            o_author = html_escape(str(orig["screen_name"] or "原帖作者"))
            o_text = orig["text"] or ""
            # 原帖文字：过滤"此微博已不可见"占位，其余渲染
            if "此微博已不可见" in o_text or "抱歉" in o_text[:12]:
                o_body = ""
            else:
                o_body = fmt_text(o_text, q)
            if o_body or orig_imgs_html or o_video_html:
                orig_block = (
                    f'<div class="orig-box">'
                    f'<div class="orig-tag">原帖 · {o_author}</div>'
                    f'{f"<div class=orig-text>{o_body}</div>" if o_body else ""}'
                    f'{orig_imgs_html}'
                    f'{o_video_html}'
                    f'</div>'
                )
        else:
            # 原博不在本地库：给"查看原帖"跳转兜底，不再空白
            o_rid = html_escape(str(w["retweet_id"]))
            orig_block = (
                f'<div class="orig-box orig-miss">'
                f'<div class="orig-tag">原帖 · 未备份</div>'
                f'<a class="orig-link" href="https://m.weibo.cn/detail/{o_rid}" '
                f'target="_blank" rel="noopener">查看原帖 ↗</a>'
                f'</div>'
            )
    elif _rt_text:
        # md 恢复的历史数据没有原帖 id：用库里存的转发原文兜底，样式与原帖块一致
        _rt_body = re.sub(r"^\s*转发[:：]\s*", "", _rt_text)
        # md 里原帖的图是 ![](img/xxx.jpg) 形式的 markdown，
        # 这些图本地都有，不能当文字显示 —— 抽出来按九宫格渲染
        _rt_imgs = re.findall(r"!\[[^\]]*\]\(img/([^)]+)\)", _rt_body)
        _rt_body = re.sub(r"!\[[^\]]*\]\(img/[^)]+\)", "", _rt_body)
        _rt_body = re.sub(r"\n{3,}", "\n\n", _rt_body).strip()
        _rt_imgs_html = ""
        if _rt_imgs:
            _cells = "".join(
                f'<div class="ph"><img loading="lazy" src="/img/{quote(fn)}" '
                f'onclick="wbLightbox(this)"></div>' for fn in _rt_imgs)
            _rt_imgs_html = (
                f'<div class="pics { "p1" if len(_rt_imgs) == 1 else ("p2" if len(_rt_imgs) == 2 else "") }">{_cells}</div>')
        orig_block = (
            f'<div class="orig-box">'
            f'<div class="orig-tag">原帖 · 转发内容</div>'
            f'{f"<div class=orig-text>{fmt_text(norm_md_links(_rt_body), q)}</div>" if _rt_body else ""}'
            f'{_rt_imgs_html}'
            f'</div>'
        )

    # 评论预览（前5条热度高的，带头像+时间戳+IP属地）
    con = get_db()
    comments = con.execute(
        "SELECT user_screen_name, user_avatar_url, text, like_count, created_at, ip_location FROM comments "
        "WHERE weibo_id=? ORDER BY like_count DESC LIMIT 5",
        (str(w["id"]),),
    ).fetchall()
    # 评论总数（用于"展开全部"按钮）
    c_total = con.execute(
        "SELECT COUNT(*) FROM comments WHERE weibo_id=?", (str(w["id"]),)
    ).fetchone()[0]
    con.close()
    comments_html = ""
    if comments:
        items = ""
        for c in comments:
            c_avatar = html_escape(c["user_avatar_url"] or "")
            # 时间戳精确到分秒
            c_time = html_escape(fmt_time(c["created_at"]))
            c_ip = html_escape(str(c["ip_location"] or "").strip())
            ip_html = f'<span class="cmt-ip">{c_ip}</span>' if c_ip else ""
            items += (
                f'<div class="cmt">'
                f'<img class="cmt-av" src="{c_avatar}" referrerpolicy="no-referrer" '
                f'onerror="this.style.display=\'none\'">'
                f'<div class="cmt-body">'
                f'<div class="cmt-hd"><b>{html_escape(c["user_screen_name"] or "网友")}</b>'
                f'<span class="cmt-t">{c_time}</span>{ip_html}</div>'
                f'<div class="cmt-tx">{fmt_text(c["text"])}</div>'
                f'</div></div>'
            )
        comments_html = f'<div class="cmts">{items}</div>'
        # 若库中评论多于预览条数，提供"展开全部评论"入口（懒加载）
        if c_total > 5:
            comments_html += (
                f'<div class="cmt-more">'
                f'<button class="cmt-expand" data-wid="{html_escape(str(w["id"]))}" '
                f'data-total="{c_total}" onclick="expandComments(this)">'
                f'展开全部 {c_total} 条评论 ▾'
                f'</button>'
                f'<div class="cmt-all" style="display:none"></div>'
                f'</div>'
            )

    stats = []
    if w["attitudes_count"]:
        stats.append(f'赞 {w["attitudes_count"]}')
    if w["comments_count"]:
        stats.append(f'评论 {w["comments_count"]}')
    if w["reposts_count"]:
        stats.append(f'转发 {w["reposts_count"]}')

    # 正文：把“查看图片”占位转成可点击蓝色链接（指向本地已下载的图，多图显示张数）
    _wtext = norm_md_links(w["text"] or "")
    body_html = fmt_text(_wtext, q)
    if "查看图片" in _wtext:
        link_href = ""
        if local_imgs:
            link_href = "/img/" + quote(local_imgs[0])
        elif pics:
            link_href = pics[0]
        if link_href:
            pic_total = len(local_imgs) or len(pics)
            label = f"查看图片（{pic_total}张）" if pic_total > 1 else "查看图片"
            view_link = (
                f'<a class="viewpic" href="{html_escape(link_href)}" '
                f'target="_blank">{html_escape(label)}</a>'
            )
            body_html = body_html.replace("查看图片", view_link)

    # 头条文章：把正文里的“网页链接”占位转成指向文章的可点击链接
    if w["article_url"]:
        art_link = (
            f'<a class="viewpic" href="{html_escape(str(w["article_url"]))}" '
            f'target="_blank">网页链接</a>'
        )
        body_html = body_html.replace("网页链接", art_link)

    # 地点：正文里的地点文字 -> 可点击链接（优先库内 location_url，兜底微博地点搜索）
    loc_text = (w["location"] or "").strip()
    if loc_text and loc_text in _wtext:
        loc_url = ""
        try:
            if "location_url" in w.keys():
                loc_url = w["location_url"] or ""
        except Exception:
            loc_url = ""
        if loc_url:
            loc_href = str(loc_url)
        else:
            loc_href = "https://s.weibo.com/weibo?q=" + quote(loc_text)
        loc_a = (
            f'<a class="loc-link" href="{html_escape(loc_href)}" '
            f'target="_blank" rel="noopener">{html_escape(loc_text)}</a>'
        )
        body_html = body_html.replace(html_escape(loc_text), loc_a)

    # IP 属地（2022 年后微博自带，老数据从 md/接口补）
    try:
        _region = str(w["region"] or "").strip()
    except Exception:
        _region = ""
    region_html = (f'<span class="wb-region">{html_escape(_region)}</span>'
                   if _region else "")

    # 视频：本地优先（video/<时间戳>.mp4），没有就提示去微博看
    _vts = str(w["created_at"]) if w["created_at"] else ""
    _vfile = find_local_video(cur_user_id, _vts) if _vts else ""
    video_html = ""
    if _vfile:
        video_html = (
            f'<div class="wb-video"><video controls preload="metadata" playsinline '
            f'src="/video/{quote(_vfile)}"></video></div>'
        )
    else:
        try:
            _vu = (w["video_url"] or "").strip()
        except Exception:
            _vu = ""
        if _vu:
            video_html = (
                f'<div class="wb-video-miss">🎬 本地没存这条视频，'
                f'<a href="https://m.weibo.cn/detail/{html_escape(str(w["id"]))}" '
                f'target="_blank" rel="noopener">去微博看原视频 ↗</a></div>'
            )

    # 自定义标签
    _tags = tags_of(w["id"])
    tag_html = ('<div class="wb-tags">'
                + "".join(
                    f'<a class="wb-tag" href="/?user={cur_user_id}&tag={quote(str(t))}" '
                    f'title="查看该标签下的微博">{html_escape(str(t))}</a>'
                    for t in _tags)
                + f'<span class="wb-tag add" data-wid="{html_escape(str(w["id"]))}" '
                  f'title="给这条加标签">＋ 标签</span></div>')

    return f"""
    <article class="card" data-ts="{html_escape(_vts)}" data-wid="{html_escape(str(w["id"]))}">
      <div class="hd">
        {avatar_html}
        <div class="who">
          <div class="nick">{html_escape(nick)}</div>
          <div class="meta">{html_escape(created)} · {html_escape(w["source"] or "")}{region_html}</div>
        </div>
      </div>
      <div class="bd">{body_html}</div>
      {imgs_html}
      {video_html}
      {orig_block}
      {tag_html}
      <div class="ft">
        <span class="stats">{ " · ".join(stats) }</span>
        <a class="link" href="https://m.weibo.cn/detail/{html_escape(w["id"])}" target="_blank">原帖 ↗</a>
        <a class="link" href="/share/{html_escape(str(w["id"]))}.png" target="_blank" title="生成一张分享图">分享图 ↗</a>
      </div>
      {comments_html}
    </article>
    """

def render_fav_card(f):
    """收藏卡片：作者是收藏的博主，展示正文+本地图+作者主页链接"""
    nick = html_escape(str(f["author_nick"] or "未知博主"))
    uid = html_escape(str(f["author_uid"] or ""))
    fav_time = html_escape(str(f["time"] or ""))
    # 头像：无 URL，用首字符圆块
    first = (str(f["author_nick"] or "博")[0:1])
    avatar_html = f'<div class="fav-av">{html_escape(first)}</div>'
    body_html = fmt_text(f["text"])
    imgs_html = ""
    try:
        imgs = json.loads(f["imgs"] or "[]")
    except Exception:
        imgs = []
    if imgs:
        cells = ""
        for name in imgs:
            src = "/fav_img/" + quote(str(name))
            cells += (
                f'<div class="ph"><img loading="lazy" src="{html_escape(src)}" '
                f'onerror="this.parentNode.style.display=\'none\'" '
                f'onclick="wbLightbox(this)"></div>'
            )
        imgs_html = f'<div class="pics {"p1" if len(imgs)==1 else ("p2" if len(imgs)==2 else "")}">{cells}</div>'
    home = f"https://weibo.com/u/{uid}" if uid else "#"
    try:
        wid = str(f["weibo_id"] or "")
    except Exception:
        wid = ""
    post_link = (
        f'<a class="link" href="https://m.weibo.cn/detail/{html_escape(wid)}" '
        f'target="_blank">原帖 ↗</a>' if wid else ""
    )
    owner = str(f["owner_uid"] or "")
    _ftags = tags_of(wid) if wid else []
    tag_html = ""
    if wid:
        tag_html = ('<div class="wb-tags">'
                    + "".join(
                        f'<a class="wb-tag" href="/?user={owner}&tag={quote(str(t))}">'
                        f'{html_escape(str(t))}</a>' for t in _ftags)
                    + f'<span class="wb-tag add" data-wid="{html_escape(wid)}" '
                      f'title="给这条加标签">＋ 标签</span></div>')
    return f"""
    <article class="card">
      <div class="hd">
        {avatar_html}
        <div class="who">
          <div class="nick">{nick}</div>
          <div class="meta">发布于 {fav_time} · 📌 收藏夹</div>
        </div>
      </div>
      <div class="bd">{body_html}</div>
      {imgs_html}
      {tag_html}
      <div class="ft">
        <span class="stats">📌 已收藏</span>
        {post_link}
        <a class="link" href="{home}" target="_blank">作者主页 ↗</a>
      </div>
    </article>
    """

def render_index_html(nick, user_id, total, cards, options, q_esc, d1, d2, ftype, qs, page, page_count, pager, fav, view="", view_head="", view_kwargs="", cnt_label=""):
    vhidden = ""
    if view:
        vhidden = f'<input type="hidden" name="view" value="{view}">'
        if view_kwargs:
            for _k, _v in view_kwargs.items():
                if _v:
                    vhidden += f'<input type="hidden" name="{_k}" value="{_v}">'
    if fav:
        search_form = (
            f'<form class="search-form" method="get" action="/">'
            f'<input type="hidden" name="user" value="{user_id}">'
            f'<input type="hidden" name="fav" value="1">'
            f'<input type="text" name="q" value="{q_esc}" placeholder="搜索收藏内容">'
            f'<button type="submit">搜索</button>'
            f'<a class="btn" href="/?user={user_id}&fav=1" title="清除筛选">重置</a>'
            f'</form>'
        )
    else:
        search_form = (
            f'<form class="search-form" method="get" action="/">'
            f'<input type="hidden" name="user" value="{user_id}">'
            f'{vhidden}'
            f'<input type="text" name="q" value="{q_esc}" placeholder="搜索关键词" title="搜索微博正文关键词">'
            f'<input type="date" name="d1" value="{d1}" title="起始日期">'
            f'<span class="sep">至</span>'
            f'<input type="date" name="d2" value="{d2}" title="结束日期">'
            f'<select name="type" title="微博类型筛选" onchange="this.form.submit()">'
            f'<option value="" {"selected" if not ftype else ""}>全部类型</option>'
            f'<option value="orig" {"selected" if ftype=="orig" else ""}>原创</option>'
            f'<option value="retweet" {"selected" if ftype=="retweet" else ""}>转发</option>'
            f'<option value="article" {"selected" if ftype=="article" else ""}>文章</option>'
            f'<option value="liked" {"selected" if ftype=="liked" else ""}>有获赞</option>'
            f'<option value="commented" {"selected" if ftype=="commented" else ""}>有评论</option>'
            f'<option value="reposted" {"selected" if ftype=="reposted" else ""}>有转发互动</option>'
            f'</select>'
            f'<button type="submit">搜索</button>'
            f'<a class="btn" href="/?user={user_id}" title="清除筛选">重置</a>'
            f'<a class="btn" href="/export.md?{qs}" title="把当前筛选结果导出成 Markdown">导出 MD</a>'
            f'<a class="btn" href="javascript:window.print()" title="打印或另存为 PDF">打印/PDF</a>'
            f'</form>'
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#e6162d">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="微博归档">
<title>微博归档阅读器 - {html_escape(nick)}</title>
  <link rel="manifest" href="/static/manifest.json">
  <link rel="apple-touch-icon" href="/static/icon-192.png">
  <link rel="icon" href="/static/icon-192.png">
  <link rel="stylesheet" href="{STATIC_CSS}">
</head><body>
<div class="glow-veil"></div>
<div class="top">
  <h1>微博归档阅读器</h1>
  <select id="userSel" onchange="switchUser()">{options}</select>
  <span class="cnt">{cnt_label or f"共 {total} 条"}</span>
  {search_form}
  <button class="btn" id="openSet" onclick="toggleSettings()">🎨 外观设置</button>
</div>

<div class="layout">
<aside class="side">
  <a class="side-it {'on' if not fav and not view else ''}" href="/?user={user_id}" title="回到时间线">📄 时间线</a>
  <a class="side-it {'on' if fav else ''}" href="/?user={user_id}&fav=1" title="查看收藏夹">📌 收藏</a>
  <a class="side-it {'on' if view=='onthisday' else ''}" href="/?user={user_id}&view=onthisday" title="往年今天发的微博">📅 那年今日</a>
  <a class="side-it {'on' if view=='yearbook' else ''}" href="/?user={user_id}&view=yearbook" title="按年浏览与统计">📚 年鉴</a>
  <a class="side-it {'on' if view=='graph' else ''}" href="/?user={user_id}&view=graph" title="互动最多的账号图谱">🕸️ 互动图谱</a>
  <a class="side-it {'on' if view=='report' else ''}" href="/?user={user_id}&view=report" title="年度数据报告与词云">📊 年度报告</a>
  <a class="side-it {'on' if view=='health' else ''}" href="/?user={user_id}&view=health" title="归档完整性体检">🩺 体检</a>
  <a class="side-it {'on' if view=='tags' else ''}" href="/?user={user_id}&view=tags" title="自定义标签合集">🏷 合集</a>
</aside>
<main class="wrap">
  {view_head}
  {cards}
  {pager}
</main>
</div>

<div class="settings" id="settingsPanel">
  <h3>网页背景（26 种）</h3>
  <div class="group">
    <div class="row" data-target="page" id="pageOpts"></div>
    <div class="slider-row">
      <span>强度</span>
      <input type="range" id="pageStr" min="0" max="100" value="55">
      <span class="val" id="pageStrV">55</span>
    </div>
    <div id="bgUploadRow" style="display:none">
      <div class="row" data-target="bgfit">
        <div class="opt" data-v="contain">居中</div>
        <div class="opt" data-v="cover">扩展</div>
        <div class="opt" data-v="fill">裁剪</div>
      </div>
      <div class="dropzone" id="bgDrop">
        <div class="dz-icon">🖼️</div>
        <div class="dz-main">点击选择图片</div>
        <div class="dz-hint">支持 jpg / png / webp，10MB 以内</div>
      </div>
      <input type="file" id="bgFile" accept="image/*" style="display:none">
      <div class="hint">居中=完整显示留白 · 扩展=等比铺满裁边 · 裁剪=拉伸铺满<br>强度滑条=遮罩深浅（保证文字可读）</div>
    </div>
    <div class="hint">只有玻璃、磨砂、液态这三种会用到强度，它控制光晕的浓淡；其它风格几乎没变化</div>
  </div>
  <h3>文本框背景（25 种） <button id="linkTheme" title="点击锁定：跟随网页背景" style="margin-left:6px;border:1px solid rgba(120,135,160,.4);background:transparent;border-radius:8px;padding:1px 8px;cursor:pointer;font-size:12px;color:inherit">🔀</button></h3>
  <div class="group">
    <div class="row" data-target="card" id="cardOpts"></div>
    <div class="slider-row">
      <span>强度</span>
      <input type="range" id="cardStr" min="0" max="100" value="70">
      <span class="val" id="cardStrV">70</span>
    </div>
    <div class="hint">玻璃质感：数值越大越发白不透明，调到 0 时最通透</div>
  </div>
  <h3>图表配色</h3>
  <div class="group">
    <div class="row" data-target="chart" id="chartOpts"></div>
    <div class="hint">年度报告柱状图渐变、互动标签、排名圆标与词云主色跟随此色；深浅渐变自动保留</div>
  </div>
  <h3>布局</h3>
  <div class="group">
    <div class="slider-row">
      <span>宽度</span>
      <input type="range" id="wrapW" min="560" max="1000" step="10" value="720">
      <span class="val" id="wrapWV">720</span>
    </div>
    <div class="hint">网页内容区宽度（560–1000px），越大每屏看的越多</div>
    <div class="slider-row">
      <span>字号</span>
      <input type="range" id="fontS" min="14" max="20" step="1" value="15">
      <span class="val" id="fontSV">15</span>
    </div>
    <div class="hint">正文与评论字号（14–20px）</div>
    <div class="slider-row">
      <span>字体</span>
      <select id="fontF">
        <option value="default">默认（微软雅黑）</option>
        <option value="yahei">微软雅黑</option>
        <option value="song">宋体（衬线）</option>
        <option value="kai">楷体</option>
        <option value="hei">黑体</option>
        <option value="yuan">幼圆</option>
        <option value="mono">等宽（Consolas）</option>
        <option value="georgia">Georgia 衬线</option>
        <option value="custom">✏️ 自定义…</option>
      </select>
    </div>
    <div id="fontCustomRow" style="display:none">
      <input id="fontCustom" list="wbFontDatalist" type="text" placeholder="点这里选，或输入字体名过滤（如 思源 / AaHuaBan）"
             style="width:100%;box-sizing:border-box;padding:6px 10px;border-radius:8px;
                    border:1px solid rgba(120,135,160,.35);background:transparent;color:inherit;font-size:13px">
      <datalist id="wbFontDatalist"></datalist>
      <div class="hint" style="margin-top:4px">
        下拉里是本机已装的 400 多个字体（显示的是<b>家族名</b>，不是文件名）。
        比如 <code>12857.ttf</code> 的家族名是 <code>AaHuaBan (Non-Commercial Use)</code>。
        输入几个字就能过滤；逗号分隔可写多个候选按顺序回退。
      </div>
    </div>
    <div class="hint">正文字体，切换立即生效并自动记住</div>
  </div>
  <div class="style-tip" id="styleTip"></div>
  <div class="reset" onclick="resetSettings()">恢复默认设置</div>
</div>

  <script src="{STATIC_JS}"></script></body></html>"""
    return html

def _mk_options(users, user_id):
    options = ""
    for uid, n in users:
        sel = " selected" if uid == user_id else ""
        options += f'<option value="{uid}"{sel}>{html_escape(n)}（{uid}）</option>'
    return options

def _mk_pager(qs, page, page_count, total):
    if page_count <= 1:
        return ""
    prev_dis = 'style="pointer-events:none;opacity:.4"' if page <= 1 else ""
    nxt_dis = 'style="pointer-events:none;opacity:.4"' if page >= page_count else ""
    return (
        f'<div class="pager">'
        f'<a href="/?{qs}&page={page-1}" {prev_dis}>← 上一页</a>'
        f'<span>{page} / {page_count}（共 {total} 条）</span>'
        f'<a href="/?{qs}&page={page+1}" {nxt_dis}>下一页 →</a>'
        f'</div>'
    )
