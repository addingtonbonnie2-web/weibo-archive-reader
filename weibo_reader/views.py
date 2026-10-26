# -*- coding: utf-8 -*-
"""视图层：那年今日 / 年鉴 / 互动图谱 / 年度报告 / 体检 / 合集。"""

import os
import re
from datetime import datetime
from urllib.parse import quote

from .core import (
    fmt_text,
    get_db,
    html_escape,
    user_folder,
)
from .render import (
    _mk_options,
    _mk_pager,
    render_index_html,
    render_weibo,
)

# ==================== 功能视图：那年今日 / 年鉴 / 互动图谱 / 年度报告 ====================

def _view_head(title_html):
    return f'<div class="view-head">{title_html}</div>'

def view_onthisday(user_id, nick, users, users_map, q):
    """📅 那年今日：往年同月同日的微博，按年份分组展示"""
    today = datetime.now()
    md = today.strftime("%m-%d")
    con = get_db()
    where = ["user_id=?", "substr(created_at,6,5)=?"]
    args = [user_id, md]
    if q:
        where.append("text LIKE ?")
        args.append("%" + q + "%")
    rows = con.execute(
        f"SELECT * FROM weibo WHERE {' AND '.join(where)} ORDER BY created_at DESC",
        args,
    ).fetchall()
    con.close()

    # 按年份分组
    groups = {}
    for r in rows:
        y = str(r["created_at"])[:4] or "未知"
        groups.setdefault(y, []).append(r)
    years = sorted(groups.keys(), reverse=True)

    cards = ""
    for y in years:
        inner = "".join(render_weibo(r, users_map, user_id, q) for r in groups[y])
        cards += (
            f'<div class="otd-year">{y} 年 · {md}'
            f'<span class="num">（{len(groups[y])} 条）</span></div>{inner}'
        )
    if not cards:
        cards = '<div class="empty">往年今天还没有发过微博</div>'

    total = len(rows)
    head = _view_head(
        f'📅 <b>那年今日</b> · {today.month}月{today.day}日 — 往年今日共 <b>{total}</b> 条，跨 {len(years)} 个年份'
    )
    options = _mk_options(users, user_id)
    qs = f"user={user_id}&view=onthisday" + (f"&q={quote(q)}" if q else "")
    return render_index_html(nick, user_id, total, cards, options, html_escape(q), "", "", "", qs, 1, 1, "", False,
                             view="onthisday", view_head=head)

def view_yearbook(user_id, nick, users, users_map, year, month, q, page):
    """📚 年鉴：按年份浏览，顶部年度统计 + 年份导航"""
    con = get_db()
    # 该账号有数据的年份列表
    years = [r[0] for r in con.execute(
        "SELECT DISTINCT substr(created_at,1,4) y FROM weibo WHERE user_id=? AND created_at IS NOT NULL ORDER BY y DESC",
        (user_id,),
    ).fetchall()]
    if year not in years:
        year = years[0] if years else ""

    where = ["user_id=?"]
    args = [user_id]
    if year:
        where.append("substr(created_at,1,4)=?")
        args.append(year)
    if month:
        where.append("substr(created_at,6,2)=?")
        args.append(month)
    if q:
        where.append("text LIKE ?")
        args.append("%" + q + "%")
    wsql = " AND ".join(where)

    total = con.execute(f"SELECT COUNT(*) FROM weibo WHERE {wsql}", args).fetchone()[0]
    # 年度统计
    st = con.execute(
        f"SELECT "
        f"SUM(CASE WHEN retweet_id IS NULL OR retweet_id='' THEN 1 ELSE 0 END) orig,"
        f"SUM(CASE WHEN retweet_id IS NOT NULL AND retweet_id!='' THEN 1 ELSE 0 END) rt,"
        f"SUM(CASE WHEN article_url IS NOT NULL AND article_url!='' THEN 1 ELSE 0 END) art,"
        f"SUM(attitudes_count) likes, SUM(comments_count) cmts, SUM(reposts_count) rps,"
        f"SUM(CASE WHEN attitudes_count > 0 THEN 1 ELSE 0 END) liked_n,"
        f"SUM(CASE WHEN comments_count > 0 THEN 1 ELSE 0 END) cmt_n,"
        f"SUM(CASE WHEN reposts_count > 0 THEN 1 ELSE 0 END) rps_n "
        f"FROM weibo WHERE {wsql}",
        args,
    ).fetchone()
    rows = con.execute(
        f"SELECT * FROM weibo WHERE {wsql} ORDER BY created_at DESC LIMIT 20 OFFSET ?",
        args + [(page - 1) * 20],
    ).fetchall()
    # 月份列表（在关闭连接前查好）
    months = []
    if year:
        months = [r[0] for r in con.execute(
            "SELECT DISTINCT substr(created_at,6,2) m FROM weibo WHERE user_id=? AND substr(created_at,1,4)=? ORDER BY m",
            (user_id, year),
        ).fetchall()]
    con.close()

    cards = "".join(render_weibo(r, users_map, user_id, q) for r in rows) or (
        '<div class="empty">该年份还没有微博记录</div>'
    )

    # 年份导航
    ynav = ""
    for y in years:
        on = ' class="on"' if y == year else ""
        ynav += f'<a{on} href="/?user={user_id}&view=yearbook&year={y}">{y}</a>'
    ynav_html = f'<div class="yb-nav">{ynav}</div>' if ynav else ""

    # 月份导航
    mnav = ""
    if year:
        mnav = '<a href="/?user={}&view=yearbook&year={}"{}>全部</a>'.format(
            user_id, year, '' if not month else '')
        for m in months:
            on = ' class="on"' if month == m else ""
            mnav += f'<a{on} href="/?user={user_id}&view=yearbook&year={year}&month={m}">{int(m)}月</a>'
        mnav = f'<div class="yb-nav">{mnav}</div>'

    orig_n = st["orig"] or 0
    rt_n = st["rt"] or 0
    art_n = st["art"] or 0
    likes = st["likes"] or 0
    cmts = st["cmts"] or 0
    rps = st["rps"] or 0
    # 统计卡：点一下就跳到时间线，并按「年份/月份 + 对于类型」筛选
    def _stat_href(ftype=""):
        p = [f"user={user_id}"]
        if year:
            if month:
                p.append("d1=%s-%s-01" % (year, month))
                p.append("d2=%s-%s-31" % (year, month))
            else:
                p.append("d1=%s-01-01" % year)
                p.append("d2=%s-12-31" % year)
        if q:
            p.append("q=" + quote(q))
        if ftype:
            p.append("type=" + ftype)
        return "/?" + "&".join(p)

    def _stat(num, label, ftype="", sub=0):
        tip = f"点击查看「{label}」对应的微博"
        if sub:
            tip = f"共 {num} 条，其中{label} {sub} 条，点击查看"
        return (
            f'<a class="yb-stat" href="{_stat_href(ftype)}" title="{tip}">'
            f'<div class="n">{num}</div><div class="l">{label}</div></a>'
        )

    stats = (
        f'<div class="yb-stats">'
        + _stat(total, "总条数")
        + _stat(orig_n, "原创", "orig")
        + _stat(rt_n, "转发", "retweet")
        + _stat(art_n, "文章", "article")
        + _stat(likes, "获赞", "liked", st["liked_n"] or 0)
        + _stat(cmts, "评论", "commented", st["cmt_n"] or 0)
        + _stat(rps, "转发互动", "reposted", st["rps_n"] or 0)
        + f'</div>'
    )

    head = _view_head(f'📚 <b>年鉴</b> · {year or "全部年份"} — 共 <b>{total}</b> 条')
    options = _mk_options(users, user_id)
    qs = f"user={user_id}&view=yearbook" + (f"&year={year}" if year else "") + (f"&month={month}" if month else "") + (f"&q={quote(q)}" if q else "")
    page_count = max(1, (total + 19) // 20)
    pager = _mk_pager(qs, page, page_count, total)
    body = ynav_html + mnav + stats + cards + pager
    return render_index_html(nick, user_id, total, body, options, html_escape(q), "", "", "", qs, page, page_count, pager, False,
                             view="yearbook", view_head=head)

def view_graph(user_id, nick, users, users_map):
    """🕸️ 互动图谱：我转发最多的原帖作者 / 评论我最多的人 / 我最常@的人"""
    con = get_db()
    # 1) 我转发的原帖作者 Top（转发计数）
    rows_rt = con.execute(
        "SELECT o.screen_name n, COUNT(*) c FROM weibo w "
        "JOIN weibo o ON o.id = w.retweet_id "
        "WHERE w.user_id=? AND o.screen_name IS NOT NULL AND o.screen_name!='' "
        "GROUP BY o.screen_name ORDER BY c DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    # 2) 评论我最多的人 Top
    rows_cm = con.execute(
        "SELECT c.user_screen_name n, COUNT(*) c FROM comments c "
        "JOIN weibo w ON w.id = c.weibo_id "
        "WHERE w.user_id=? AND c.user_screen_name IS NOT NULL AND c.user_screen_name!='' "
        "GROUP BY c.user_screen_name ORDER BY c DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    # 3) 我最常 @ 的人 Top（从 at_users 字段统计）
    rows_at = con.execute(
        "SELECT at_users FROM weibo WHERE user_id=? AND at_users IS NOT NULL AND at_users!=''",
        (user_id,),
    ).fetchall()
    con.close()

    at_cnt = {}
    for r in rows_at:
        for name in str(r["at_users"]).replace("，", ",").split(","):
            name = name.strip()
            if name and name != nick:
                at_cnt[name] = at_cnt.get(name, 0) + 1
    at_top = sorted(at_cnt.items(), key=lambda x: -x[1])[:10]

    def _rank_html(items, empty_txt):
        if not items:
            return f'<div class="empty">{empty_txt}</div>'
        mx = max(x[1] for x in items)
        out = ""
        for n, c in items:
            pct = int(c / mx * 100) if mx else 0
            out += (
                f'<div class="g-item">'
                f'<span class="g-name" title="{html_escape(n)}">{html_escape(n)}</span>'
                f'<div class="g-bar"><div class="g-fill" style="width:{pct}%"></div></div>'
                f'<span class="g-n">{c}</span>'
                f'</div>'
            )
        return out

    cards = (
        f'<div class="graph-wrap">'
        f'<div class="graph-card"><h3>🔁 我转发过的原帖作者 Top</h3>'
        f'{_rank_html([(r["n"], r["c"]) for r in rows_rt], "还没有转发记录")}</div>'
        f'<div class="graph-card"><h3>💬 评论我最多的人 Top</h3>'
        f'{_rank_html([(r["n"], r["c"]) for r in rows_cm], "还没有评论记录")}</div>'
        f'<div class="graph-card" style="grid-column:1/-1"><h3>📣 我最常 @ 的人 Top</h3>'
        f'{_rank_html(at_top, "还没有 @ 记录")}</div>'
        f'</div>'
    )
    head = _view_head('🕸️ <b>互动图谱</b> — 与你有来有往的账号（按互动次数排序）')
    options = _mk_options(users, user_id)
    return render_index_html(nick, user_id, 0, cards, options, "", "", "", "", "", 1, 1, "", False,
                             view="graph", view_head=head)

def view_report(user_id, nick, users, users_map, year, q):
    """📊 年度报告：年度统计 KPI + 月度/时段分布 + 最热微博 + 词云（jieba）"""
    con = get_db()
    years = [r[0] for r in con.execute(
        "SELECT DISTINCT substr(created_at,1,4) y FROM weibo WHERE user_id=? AND created_at IS NOT NULL ORDER BY y DESC",
        (user_id,),
    ).fetchall()]
    if year not in years:
        year = years[0] if years else ""

    where = ["user_id=?"]
    args = [user_id]
    if year:
        where.append("substr(created_at,1,4)=?")
        args.append(year)
    wsql = " AND ".join(where)

    total = con.execute(f"SELECT COUNT(*) FROM weibo WHERE {wsql}", args).fetchone()[0]
    st = con.execute(
        f"SELECT "
        f"SUM(CASE WHEN retweet_id IS NULL OR retweet_id='' THEN 1 ELSE 0 END) orig,"
        f"SUM(CASE WHEN retweet_id IS NOT NULL AND retweet_id!='' THEN 1 ELSE 0 END) rt,"
        f"SUM(CASE WHEN article_url IS NOT NULL AND article_url!='' THEN 1 ELSE 0 END) art,"
        f"SUM(attitudes_count) likes, SUM(comments_count) cmts, SUM(reposts_count) rps,"
        f"COUNT(DISTINCT substr(created_at,1,7)) months "
        f"FROM weibo WHERE {wsql}",
        args,
    ).fetchone()
    # 月度分布
    mdist = con.execute(
        f"SELECT substr(created_at,6,2) m, COUNT(*) c FROM weibo WHERE {wsql} GROUP BY m ORDER BY m",
        args,
    ).fetchall()
    # 小时分布
    hdist = con.execute(
        f"SELECT substr(created_at,12,2) h, COUNT(*) c FROM weibo WHERE {wsql} GROUP BY h ORDER BY h",
        args,
    ).fetchall()
    # 最热微博 Top5（按互动总数）
    hot = con.execute(
        f"SELECT * FROM weibo WHERE {wsql} "
        f"ORDER BY (COALESCE(attitudes_count,0)+COALESCE(comments_count,0)+COALESCE(reposts_count,0)) DESC LIMIT 5",
        args,
    ).fetchall()
    # 词云：取该年全部正文
    alltext = con.execute(
        f"SELECT text FROM weibo WHERE {wsql} AND text IS NOT NULL", args
    ).fetchall()
    con.close()

    # ---------- 词云：jieba 分词 ----------
    word_top = []
    if alltext:
        try:
            import jieba
            from collections import Counter
            stop = set("""的 了 是 我 你 他 她 它 们 这 那 就 都 也 很 会 要 有 没 不 还 又 和 与 及 或 但 而 被 把 让 给 从 对 向 为 以 于 之 其 此 中 等 啊 吧 吗 呢 哦 嗯 哈 啦 呀 微博 转发 图片 视频 今天 明天 昨天 现在 时候 什么 怎么 为什么 可以 不能 没有 真的 感觉 觉得 知道 喜欢 希望 不要 不是 就是 已经 还是 一个 这个 那个 自己 我们 你们 他们 大家 东西 事情 问题 网页 链接 查看 谢谢 哈哈 哈哈哈 呜呜 呜呜呜 真的吗 好喜欢 好想 好好 有点 一些 一点 一下 一次 一起 一直 一边 一样 一定 一年 一天 一月 人 时间 日子 生活 工作 学习 说 想 看 听 写 去 来 里 上 下 前 后 中 更 最 太 非常 特别 超级 比较 差不多 大概 可能 应该 必须 需要 不会 不要 不用 没什么 怎样 如何 哪里 谁 吧 吗 呢 啊 呀 哦 嗯 哈 啦 了 是 不 我 你 他 她 它 这 那 们 就 都 也 很 会 要 有 没 还 又 和 与 及 或 但 而 被 把 让 给 从 对 向 为 以 于 之 其 此 中 等 么 什么 怎么 怎样 如何 为什 为什 干嘛 咋 挺 好 真 特 太 超 巨 大 小 多 少 高 低 快 慢 行 好 行 可以 不行 没办法 想 要 说 看 听 吃 喝 玩 睡 觉 上班 下班 放假 考试 学习 复习 加班 开会 出差 旅行 回家 出门 到家 起来 过来 回去 出去 进来 出来 下来 上去 走了 来了 去了 做了 说了 看了 听了 写了 发了 拍了 买了 卖了 换了 改 了 完 了 过 了 到 了""".split())
            cnt = Counter()
            for r in alltext:
                for w in jieba.lcut(r["text"] or ""):
                    w = w.strip()
                    if len(w) < 2 or len(w) > 6:
                        continue
                    if w in stop:
                        continue
                    if w.isdigit() or w == "网页链接" or w == "查看图片":
                        continue
                    if "http" in w or "//" in w:
                        continue
                    cnt[w] += 1
            word_top = cnt.most_common(60)
        except Exception as e:
            print("wordcloud jieba error:", e)
            word_top = []

    # ---------- 组装 HTML ----------
    m_labels = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
    m_map = {r["m"]: r["c"] for r in mdist}
    mmax = max(m_map.values()) if m_map else 1
    mbar = ""
    mlabels_html = ""
    for i in range(12):
        k = f"{i+1:02d}"
        v = m_map.get(k, 0)
        h = int(v / mmax * 80) + 2
        if v:
            mbar += (f'<a class="col col-link" style="height:{h}px" '
                     f'href="/?user={user_id}&view=yearbook&year={year}&month={k}" '
                     f'title="{m_labels[i]}：{v}条（点击查看该月微博）"></a>')
            mlabels_html += (f'<a href="/?user={user_id}&view=yearbook&year={year}&month={k}" '
                             f'title="{m_labels[i]}：{v}条">{m_labels[i]}</a>')
        else:
            mbar += f'<div class="col" style="height:{h}px" title="{m_labels[i]}：0条"></div>'
            mlabels_html += f'<span title="{m_labels[i]}：0条">{m_labels[i]}</span>'
    mchart = (
        f'<div class="report-card"><h3>📆 月度发布分布 <small>点击月份查看微博</small></h3>'
        f'<div class="hbar">{mbar}</div><div class="hbar-labels">{mlabels_html}</div></div>'
    )

    h_map = {r["h"]: r["c"] for r in hdist}
    hmax = max(h_map.values()) if h_map else 1
    hbar = ""
    hlabels_html = ""
    for i in range(24):
        k = f"{i:02d}"
        v = h_map.get(k, 0)
        h = int(v / hmax * 80) + 2
        if v:
            hbar += (f'<a class="col col-link" style="height:{h}px" '
                     f'href="/?user={user_id}&hour={k}" '
                     f'title="{i}时：{v}条（点击查看该时段微博）"></a>')
            hlabels_html += (f'<a href="/?user={user_id}&hour={k}" '
                             f'title="{i}时：{v}条">{i}</a>')
        else:
            hbar += f'<div class="col" style="height:{h}px" title="{i}时：0条"></div>'
            hlabels_html += f'<span title="{i}时：0条">{i}</span>'
    hchart = (
        f'<div class="report-card"><h3>🕐 发博时段分布（24 小时） <small>点击查看该时段微博</small></h3>'
        f'<div class="hbar">{hbar}</div><div class="hbar-labels">{hlabels_html}</div></div>'
    )

    hot_html = ""
    if hot:
        items = ""
        for i, r in enumerate(hot, 1):
            it = (r["attitudes_count"] or 0) + (r["comments_count"] or 0) + (r["reposts_count"] or 0)
            tx = fmt_text((r["text"] or "")[:80])
            items += (
                f'<a class="top-item" href="/?user={user_id}&view=single&wid={r["id"]}" '
                f'title="点击查看完整微博"><span class="rk">{i}</span>'
                f'<span class="tx">{tx}</span>'
                f'<span class="st">互动 {it}</span></a>'
            )
        hot_html = (f'<div class="report-card"><h3>🔥 最热微博 Top 5 <small>点击查看完整微博</small></h3>'
                    f'<div class="report-top">{items}</div></div>')

    # 词云 HTML + JS（DOM 版，带淡入/漂浮/hover 动效，无外网依赖）
    if word_top:
        import json as _json
        wdata = _json.dumps([{"t": t, "f": c} for t, c in word_top], ensure_ascii=False)
        wc_html = (
            f'<div class="report-card"><h3>☁️ 年度词云（正文高频词）</h3>'
            f'<div id="wordcloud"></div>'
            f'<div class="wc-hint">词越大出现越多 · 悬停放大 · 自动漂浮</div></div>'
            f'<script>'
            f'(function(){{'
            f'var data={wdata};'
            f'var box=document.getElementById("wordcloud");'
            f'if(!box||!data.length)return;'
            f'var W=box.clientWidth||720,H=380;'
            f'var mx=Math.max.apply(null,data.map(function(d){{return d.f}}));'
            f'var c1=getComputedStyle(document.documentElement).getPropertyValue("--chart-c1").trim()||"#e6162d";'
            f'var c2=getComputedStyle(document.documentElement).getPropertyValue("--chart-c2").trim()||"#ff9a9e";'
            f'var cols=[c1,c2,"#c96bff","#4a9bff","#21b573","#ffb02e","#7b61ff","#f76b8a","#3aa6b9","#a05f2b"];'
            f'var placed=[];'
            f'function hit(x,y,w,h){{for(var i=0;i<placed.length;i++){{var p=placed[i];'
            f'if(x<p.x+p.w+2&&x+w+2>p.x&&y<p.y+p.h+2&&y+h+2>p.y)return true;}}return false;}}'
            f'var items=[];'
            f'data.forEach(function(d,i){{'
            f'var fs=16+Math.round(d.f/mx*44);'
            f'var el=document.createElement("a");'
            f'el.className="word-item";el.textContent=d.t;'
            f'el.href="/?user={user_id}&q="+encodeURIComponent(d.t);'
            f'el.title=d.t+" · "+d.f+" 次（点击搜索相关微博）";'
            f'el.style.fontSize=fs+"px";el.style.color=cols[i%cols.length];'
            f'el.style.opacity="0";'
            f'box.appendChild(el);'
            f'var tw=el.offsetWidth,th=el.offsetHeight;'
            f'var x=Math.random()*(W-tw),y=Math.random()*(H-th),ok=false;'
            f'for(var t=0;t<500;t++){{x=Math.random()*(W-tw);y=Math.random()*(H-th);'
            f'if(!hit(x,y,tw,th)){{ok=true;break;}}}}'
            f'if(!ok){{x=10+(i%6)*(tw+10);y=10+Math.floor(i/6)*(th+6);}}'
            f'el.style.left=x+"px";el.style.top=y+"px";'
            f'el.title=d.t+" · "+d.f+" 次";'
            f'el.dataset.delay=i*45;'
            f'placed.push({{x:x,y:y,w:tw,h:th}});'
            f'items.push(el);'
            f'}});'
            f'var anim=document.createElement("style");'
            f'anim.textContent="'
            f'@keyframes wcIn{{from{{opacity:0;transform:translateY(14px) scale(.6)}}to{{opacity:.92;transform:none}}}}'
            f'@keyframes wcFloat{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}'
            f'.word-item{{animation:wcFloat 5s ease-in-out infinite;will-change:transform;transition:transform .2s,opacity .2s;}}'
            f'.word-item:hover{{transform:scale(1.25)!important;opacity:1!important;z-index:99;}}'
            f'";'
            f'document.head.appendChild(anim);'
            f'items.forEach(function(el,i){{'
            f'setTimeout(function(){{el.style.animation="wcIn .5s ease-out both, wcFloat 5s "+((i*7)%3)+"s ease-in-out infinite";'
            f'el.style.opacity=".92";}},el.dataset.delay);'
            f'}});'
            f'}})();'
            f'</script>'
        )
    else:
        wc_html = ""

    ynav = ""
    for y in years:
        on = ' class="on"' if y == year else ""
        ynav += f'<a{on} href="/?user={user_id}&view=report&year={y}">{y}</a>'
    ynav_html = f'<div class="yb-nav">{ynav}</div>' if ynav else ""

    likes = st["likes"] or 0
    cmts = st["cmts"] or 0
    rps = st["rps"] or 0
    months_n = st["months"] or 0
    hero = (
        f'<div class="report-hero">'
        f'<h2>📊 {html_escape(nick)} 的 {year} 年度报告</h2>'
        f'<div class="sub">共 {total} 条微博 · 覆盖 {months_n} 个月 · 获赞 {likes} · 评论 {cmts} · 转发 {rps}</div>'
        f'</div>'
    )
    kpi = (
        f'<div class="report-grid">'
        f'<div class="report-kpi"><div class="v">{total}</div><div class="k">全年微博</div></div>'
        f'<div class="report-kpi"><div class="v">{st["orig"] or 0}</div><div class="k">原创</div></div>'
        f'<div class="report-kpi"><div class="v">{st["rt"] or 0}</div><div class="k">转发</div></div>'
        f'<div class="report-kpi"><div class="v">{st["art"] or 0}</div><div class="k">文章</div></div>'
        f'<div class="report-kpi"><div class="v">{likes}</div><div class="k">获赞总数</div></div>'
        f'<div class="report-kpi"><div class="v">{cmts}</div><div class="k">评论总数</div></div>'
        f'<div class="report-kpi"><div class="v">{rps}</div><div class="k">转发总数</div></div>'
        f'</div>'
    )
    cards = ynav_html + hero + kpi + mchart + hchart + hot_html + wc_html
    head = _view_head(f'📊 <b>年度报告</b> · {year or "全部年份"}（数据来自本地归档库）')
    options = _mk_options(users, user_id)
    return render_index_html(nick, user_id, total, cards, options, "", "", "", "", "", 1, 1, "", False,
                             view="report", view_head=head)

def view_health(user_id, nick, users, users_map, q):
    """🩺 体检：一眼看出归档哪里不完整（缺图/缺视频/缺原帖/孤儿文件）"""
    con = get_db()
    rows = con.execute(
        "SELECT id, created_at, pics, video_url, retweet_id FROM weibo WHERE user_id=?",
        (user_id,)).fetchall()
    total = len(rows)
    folder = user_folder(user_id) or ""
    img_dir = os.path.join(folder, "img") if folder else ""
    vid_dir = os.path.join(folder, "video") if folder else ""
    imgs = set(os.listdir(img_dir)) if img_dir and os.path.isdir(img_dir) else set()
    vids = set(os.listdir(vid_dir)) if vid_dir and os.path.isdir(vid_dir) else set()

    RE_PRE = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")

    def pre_from_name(name):
        m = RE_PRE.match(name)
        return m.group(1) if m else ""

    def pre_from_ts(ts):
        try:
            return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d_%H-%M-%S")
        except Exception:
            return ""

    img_pre = set(pre_from_name(f) for f in imgs)
    vid_pre = set(pre_from_name(f) for f in vids)
    # 关键：图片/视频文件名用的是「被转发原帖」的时间戳，
    # 而那些原帖在库里属于别的 user_id，所以这里要扫全库的时间戳。
    weibo_pre = set(pre_from_ts(r[0]) for r in
                    con.execute("SELECT created_at FROM weibo").fetchall())
    miss_vid, miss_art = [], []
    rt_missing = []
    for r in rows:
        p = pre_from_ts(r["created_at"])
        if p:
            weibo_pre.add(p)
        try:
            vu = (r["video_url"] or "").strip()
        except Exception:
            vu = ""
        if vu and p not in vid_pre:
            miss_vid.append((r["created_at"], r["id"]))
        try:
            pi = (r["pics"] or "").strip()
        except Exception:
            pi = ""
        if pi and "http" in pi and p not in img_pre:
            miss_art.append((r["created_at"], r["id"]))
        if r["retweet_id"]:
            ok = con.execute("SELECT 1 FROM weibo WHERE id=?", (str(r["retweet_id"]),)).fetchone()
            if not ok:
                rt_missing.append((r["created_at"], r["id"]))
    orphan_imgs = [f for f in imgs if pre_from_name(f) and pre_from_name(f) not in weibo_pre]
    orphan_vids = [f for f in vids if pre_from_name(f) and pre_from_name(f) not in weibo_pre]
    all_cmt = con.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    no_ip = con.execute("SELECT COUNT(*) FROM comments WHERE ip_location IS NULL "
                        "OR ip_location=''").fetchone()[0]
    con.close()

    def _kpi(n, label, color=""):
        st = f' style="color:{color}"' if color else ""
        return (f'<div class="yb-stat"><div class="n"{st}>{n}</div>'
                f'<div class="l">{label}</div></div>')

    kpi = (
        '<div class="yb-stats">'
        + _kpi(total, "微博总数")
        + _kpi(len(imgs), "本地图片")
        + _kpi(len(vids), "本地视频")
        + _kpi(len(miss_vid), "缺视频", "#d9534f" if miss_vid else "")
        + _kpi(len(miss_art), "缺图片", "#d9534f" if miss_art else "")
        + _kpi(len(rt_missing), "缺原帖", "#f0ad4e" if rt_missing else "")
        + _kpi(len(orphan_imgs), "孤儿图片", "#f0ad4e" if orphan_imgs else "")
        + _kpi(no_ip, "评论缺属地", "#999")
        + '</div>'
    )

    def _list(title, items, tip, limit=40):
        if not items:
            return (f'<div class="hb-sec"><div class="hb-t">{title}</div>'
                    f'<div class="hb-ok">✅ {tip}</div></div>')
        body = ""
        for ts, wid in items[:limit]:
            body += (f'<a class="hb-it" href="/?user={user_id}&wid={html_escape(str(wid))}" '
                     f'target="_blank">{html_escape(str(ts))}</a>')
        more = (f'<span class="hb-more">…共 {len(items)} 条，只列前 {limit} 条</span>'
                if len(items) > limit else "")
        return (f'<div class="hb-sec"><div class="hb-t">{title}'
                f'<span class="hb-n">{len(items)}</span></div>'
                f'<div class="hb-list">{body}{more}</div></div>')

    def _files(title, names, tip):
        if not names:
            return (f'<div class="hb-sec"><div class="hb-t">{title}</div>'
                    f'<div class="hb-ok">✅ {tip}</div></div>')
        sample = "、".join(html_escape(x) for x in sorted(names)[:8])
        return (f'<div class="hb-sec"><div class="hb-t">{title}'
                f'<span class="hb-n">{len(names)}</span></div>'
                f'<div class="hb-files">{sample}'
                f'{" …" if len(names) > 8 else ""}</div>'
                f'<div class="hb-tip">这些文件在硬盘上，但库里没有时间戳能对上。'
                f'常见原因有三种：转发原帖的图存在本账号目录，而原帖本身没入库；'
                f'微博已经被删除；该账号早年正文丢失，比如炸号后只剩图片。'
                f'文件都能打开，只是没有正文可配。</div></div>')

    body = (
        kpi
        + '<div class="hb-tip">体检只做统计和跳转，不会修改任何数据。'
          '缺什么就用配套的抓取脚本补，本仓库不含抓取功能。</div>'
        + _list("缺视频（有视频地址但本地没有）", miss_vid, "视频齐全")
        + _list("缺图片（有图片地址但本地没有）", miss_art, "图片齐全")
        + _list("缺原帖（转发的原帖没备份）", rt_missing, "转发原帖齐全")
        + _files("孤儿图片（本地有文件，库里没有对应微博）", orphan_imgs, "没有孤儿图片")
        + _files("孤儿视频（本地有文件，库里没有对应微博）", orphan_vids, "没有孤儿视频")
    )
    head = _view_head(f'🩺 <b>体检</b> · {html_escape(nick)} — 共 <b>{total}</b> 条')
    options = _mk_options(users, user_id)
    return render_index_html(nick, user_id, total, body, options, "", "", "", "", f"user={user_id}&view=health",
                             1, 1, "", False, view="health", view_head=head)

def view_tags(user_id, nick, users, users_map):
    """🏷 合集：本地自定义标签的总览（每个标签多少条、时间跨度）"""
    con = get_db()
    rows = con.execute(
        "SELECT t.tag, COUNT(*) c, MIN(w.created_at) a, MAX(w.created_at) b "
        "FROM weibo_tags t JOIN weibo w ON w.id=t.weibo_id "
        "WHERE w.user_id=? GROUP BY t.tag ORDER BY c DESC", (user_id,)).fetchall()
    con.close()
    if not rows:
        body = ('<div class="empty">还没有标签。<br>在任意微博卡片底部点「＋ 标签」，'
                '给它取个名字（比如「好吃的」「仓鼠」「2023 面试」），就能在这里按主题回看。</div>')
    else:
        items = ""
        for r in rows:
            items += (
                f'<a class="tb-item" href="/?user={user_id}&tag={quote(str(r["tag"]))}">'
                f'<span class="tb-name">{html_escape(str(r["tag"]))}</span>'
                f'<span class="tb-n">{r["c"]}</span>'
                f'<span class="tb-range">{html_escape(str(r["a"])[:10])} ~ '
                f'{html_escape(str(r["b"])[:10])}</span></a>'
            )
        body = f'<div class="tb-grid">{items}</div>'
    head = _view_head(f'🏷 <b>合集</b> · {html_escape(nick)} — {len(rows)} 个标签')
    options = _mk_options(users, user_id)
    return render_index_html(nick, user_id, len(rows), body, options, "", "", "", "",
                             f"user={user_id}&view=tags", 1, 1, "", False,
                             view="tags", view_head=head, cnt_label="标签")
