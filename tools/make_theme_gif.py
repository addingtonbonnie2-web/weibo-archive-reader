# -*- coding: utf-8 -*-
"""生成 README 里的主题切换动图（docs/screenshots/theme-switch.gif）。

    python tools/make_theme_gif.py

做的事：
  1. 用 tools/make_demo_db.py 那套假数据起一个临时服务（不碰你的 data/ 和 config.py）
  2. 把页面的 CSS/JS 内联、资源改绝对地址，给每个主题注入一段“强制主题”的脚本
  3. 调 Chrome 无头模式逐主题截图
  4. 拼成 GIF，每帧左下角标主题名

需要本机装有 Chrome 或 Edge；找不到会打印路径提示后直接退出，不会破坏任何文件。
主题列表在 THEMES 里改，输出路径在 DST 里改。
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)

PORT = 5062
WIDTH, HEIGHT = 980, 600
DURATION = 1300
DST = os.path.join(APP_DIR, "docs", "screenshots", "theme-switch.gif")
THEMES = [("default", "默认"), ("paper", "纸张"), ("gradient", "渐变"),
          ("aurora", "极光"), ("tech", "科技"), ("hacker", "黑客")]

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    env = os.environ.get("CHROME") or os.environ.get("BROWSER")
    for p in ([env] if env else []) + CHROME_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    return ""


def build_demo_data(work):
    """生成假数据到临时目录"""
    demo = os.path.join(work, "data")
    os.makedirs(demo, exist_ok=True)
    env = dict(os.environ, WEIBO_DATA_DIR=demo)
    r = subprocess.run([sys.executable, os.path.join(APP_DIR, "tools", "make_demo_db.py")],
                       cwd=APP_DIR, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if not os.path.isfile(os.path.join(demo, "weibo.db")):
        raise SystemExit("假数据没生成成功：\n" + (r.stdout or "") + (r.stderr or ""))
    return demo


def start_server(demo):
    """在后台线程里用临时数据目录起一个 Flask"""
    os.environ["WEIBO_DATA_DIR"] = demo
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)   # 别把访问日志刷满屏
    from weibo_reader.core import app
    from weibo_reader import routes  # noqa: F401
    th = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, threaded=True),
        daemon=True)
    th.start()
    base = "http://127.0.0.1:%d" % PORT
    for _ in range(60):
        try:
            urllib.request.urlopen(base + "/", timeout=2).read()
            return base
        except Exception:
            time.sleep(0.5)
    raise SystemExit("临时服务没起来（端口 %d 可能被占用）" % PORT)


def snapshot(base):
    """抓首页，内联 CSS/JS，资源地址改绝对"""
    page = urllib.request.urlopen(base + "/", timeout=60).read().decode("utf-8", "replace")
    for pat, cut in ((r'href="(/static/app\.css[^"]*)"', "css"),
                     (r'src="(/static/app\.js[^"]*)"', "js")):
        m = re.search(pat, page)
        if not m:
            continue
        body = urllib.request.urlopen(base + m.group(1), timeout=30).read().decode("utf-8")
        if cut == "css":
            page = re.sub(r'<link rel="stylesheet" href="[^"]*">',
                          lambda _m: "<style>\n" + body + "\n</style>", page)
        else:
            page = re.sub(r'<script src="[^"]*"></script>',
                          lambda _m: "<script>\n" + body + "\n</script>", page)
    for seg in ("img", "video", "static", "avatar", "emoji"):
        page = page.replace('src="/%s/' % seg, 'src="%s/%s/' % (base, seg))
    page = page.replace('href="/static/', 'href="%s/static/' % base)
    return page


def inject(page, theme):
    """在 head 里塞一段假 localStorage，让页面按指定主题渲染"""
    stub = (
        "<script>(function(){var want={wb_pageStyle:'%(t)s',wb_cardStyle:'%(t)s',"
        "wb_linkTheme:'1',wb_pageStr:'70',wb_fontS:'16',wb_wrapW:'760'};var real=null;"
        "try{real=window.localStorage}catch(e){}"
        "var fake={getItem:function(k){return (k in want)?want[k]:(real?real.getItem(k):null)},"
        "setItem:function(k,v){try{real&&real.setItem(k,v)}catch(e){}},"
        "removeItem:function(k){try{real&&real.removeItem(k)}catch(e){}}};"
        "try{Object.defineProperty(window,'localStorage',{value:fake,configurable:true})}"
        "catch(e){window.localStorage=fake}})();</script>" % {"t": theme})
    return page.replace("<head>", "<head>" + stub, 1) if "<head>" in page else stub + page


def shoot(chrome, src, dst):
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--hide-scrollbars", "--force-device-scale-factor=1",
           "--window-size=%d,%d" % (WIDTH, HEIGHT), "--virtual-time-budget=5000",
           "--screenshot=" + dst, "file:///" + src.replace("\\", "/")]
    subprocess.run(cmd, capture_output=True, timeout=180)
    return os.path.isfile(dst) and os.path.getsize(dst) > 1000


def compose(pairs, dst):
    """拼 GIF，每帧左下角标主题名"""
    from PIL import Image, ImageDraw, ImageFont

    font_path = r"C:\Windows\Fonts\msyh.ttc"
    if not os.path.isfile(font_path):
        font_path = r"C:\Windows\Fonts\simhei.ttf"
    frames = []
    for png, label in pairs:
        im = Image.open(png).convert("RGB")
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(font_path, 22) if os.path.isfile(font_path) else None
        bw = (int(d.textlength(label, font=f)) if f else len(label) * 22) + 34
        bh, x = 40, 18
        y = im.height - bh - 18
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=12,
                            fill=(252, 252, 254), outline=(0, 0, 0, 30))
        d.text((x + 17, y + 7), label, font=f, fill=(32, 34, 40))
        frames.append(im)

    # 统一调色板，避免逐帧量化造成整屏抖动
    sheet = Image.new("RGB", (frames[0].width, frames[0].height * len(frames)))
    for i, fr in enumerate(frames):
        sheet.paste(fr, (0, i * fr.height))
    pal = sheet.quantize(colors=256, method=Image.MEDIANCUT)
    qs = [fr.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for fr in frames]
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    qs[0].save(dst, save_all=True, append_images=qs[1:], duration=DURATION,
               loop=0, optimize=True, disposal=1)
    return os.path.getsize(dst)


def main():
    chrome = find_chrome()
    if not chrome:
        print("没找到 Chrome / Edge。装一个，或用环境变量 CHROME 指定浏览器 exe 路径。")
        return 1
    work = tempfile.mkdtemp(prefix="wb_gif_")
    try:
        demo = build_demo_data(work)
        base = start_server(demo)
        page = snapshot(base)
        pairs = []
        for theme, label in THEMES:
            html = os.path.join(work, "th_%s.html" % theme)
            png = os.path.join(work, "f_%s.png" % theme)
            io.open(html, "w", encoding="utf-8").write(inject(page, theme))
            ok = shoot(chrome, html, png)
            print("  %-9s %s" % (label, "OK" if ok else "截图失败"))
            if ok:
                pairs.append((png, label))
        if len(pairs) < 2:
            print("截图不足两张，放弃合成")
            return 1
        size = compose(pairs, DST)
        print("已生成 %s  %.1f KB  共 %d 帧" % (DST, size / 1024.0, len(pairs)))
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
