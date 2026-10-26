# -*- coding: utf-8 -*-
"""抓取微博表情图到 data/emoji/

微博的表情图在网页端只渲染"还在维护"的那批，历史联名表情（小黄人、复仇者、
星球大战、哆啦A梦早期系列……）网页已不再渲染，因此拿不到地址，只能从 App 资源里提取。

用法（在仓库根目录执行）：
    python tools/fetch_emoji.py --wid 1234567890123456       # 从某条微博补
    python tools/fetch_emoji.py --url https://weibo.com/1234567890/AbCdEf
    python tools/fetch_emoji.py --wid ... --dry              # 只看缺哪些

原理：m.weibo.cn 的 statuses/show 返回的 text 是完整 HTML，表情写成
      <img alt="[名字]" src="https://face.t.sinajs.cn/.../<slug>_mobile.png">
      按名字和本地 emoji/ 比对，缺的下载。

需要：请求带登录态。在 config.py 里加 COOKIE = "SUB=...; SUBP=..."，或设环境变量 WEIBO_COOKIE。
"""
import argparse
import json
import os
import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from weibo_reader.paths import EMOJI_DIR, CONFIG_PY  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def get_cookie():
    ck = os.environ.get("WEIBO_COOKIE", "")
    if ck:
        return ck
    if os.path.isfile(CONFIG_PY):
        try:
            ns = {}
            with open(CONFIG_PY, encoding="utf-8") as f:
                exec(compile(f.read(), CONFIG_PY, "exec"), ns)
            return str(ns.get("COOKIE") or "")
        except Exception:
            return ""
    return ""


def headers(cookie):
    return {"Cookie": cookie, "Referer": "https://m.weibo.cn/", "User-Agent": UA,
            "Accept": "application/json, text/plain, */*", "MWeibo-Pwa": "1",
            "X-Requested-With": "XMLHttpRequest"}


def resolve_wid(url):
    m = re.search(r"weibo\.com/\d+/([A-Za-z0-9]+)", url)
    if not m:
        return None
    bid = m.group(1)
    try:
        r = urllib.request.urlopen("https://m.weibo.cn/statuses/show?id=%s" % bid,
                                   timeout=20)
        return json.loads(r.read().decode("utf-8", "replace")).get("data", {}).get("id")
    except Exception:
        return None


def extract(html):
    pairs = {}
    for m in re.finditer(r"<img[^>]*>", html or ""):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if not (src and alt):
            continue
        name = re.sub(r"^\[|\]$", "", alt.group(1).strip())
        s = src.group(1)
        if name and ("face.t.sinajs.cn" in s or "/expression/" in s):
            pairs[name] = s
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wid", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    cookie = get_cookie()
    if not cookie:
        sys.exit("没有登录态：在 config.py 里加 COOKIE = \"...\"，或设 WEIBO_COOKIE")

    wid = args.wid or (resolve_wid(args.url) if args.url else None)
    if not wid:
        sys.exit("需要 --wid 或 --url")

    raw = urllib.request.urlopen(urllib.request.Request(
        "https://m.weibo.cn/statuses/show?id=%s" % wid, headers=headers(cookie)),
        timeout=30).read().decode("utf-8", "replace")
    text = (json.loads(raw).get("data") or {}).get("text") or ""
    pairs = extract(text)
    print("这条微博里识别到表情 %d 个" % len(pairs))

    os.makedirs(EMOJI_DIR, exist_ok=True)
    local = {os.path.splitext(f)[0] for f in os.listdir(EMOJI_DIR)}
    miss = {k: v for k, v in pairs.items() if k not in local}
    print("本地缺 %d 个" % len(miss))
    if args.dry:
        for k in miss:
            print("   ", k)
        return

    ok = 0
    for name, url in miss.items():
        for cand in (url, url.replace("_mobile.png", "_org.gif"),
                     url.replace("_mobile.png", "_org.png")):
            try:
                data = urllib.request.urlopen(urllib.request.Request(
                    cand, headers={"User-Agent": UA, "Referer": "https://weibo.com/"}),
                    timeout=20).read()
                if len(data) < 200:
                    continue
                ext = os.path.splitext(cand.split("?")[0])[1].lower() or ".png"
                with open(os.path.join(EMOJI_DIR, name + ext), "wb") as f:
                    f.write(data)
                ok += 1
                print("  OK %-12s %5dKB" % (name, len(data) // 1024))
                break
            except Exception:
                continue
        time.sleep(0.1)
    print("\n补到 %d 个" % ok)


if __name__ == "__main__":
    main()
