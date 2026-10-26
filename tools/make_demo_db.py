# -*- coding: utf-8 -*-
"""生成一个不含任何真实数据的 demo 库：20 条假微博 + 几条评论 + 假图片

用法（在仓库根目录执行）：
    python tools/make_demo_db.py

会创建 data/weibo.db、data/img/demo/ 下的示例图片，之后 python run.py 就能看界面。
"""
import os
import random
import sqlite3
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
  id varchar(64) NOT NULL, nick_name varchar(64) NOT NULL, gender varchar(6),
  follower_count integer, follow_count integer, birthday varchar(10),
  location varchar(32), ip_location varchar(32), edu varchar(32), company varchar(32),
  reg_date DATETIME, main_page_url text, avatar_url text, bio text, PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS weibo (
  id varchar(20) NOT NULL, bid varchar(12) NOT NULL, user_id varchar(20),
  screen_name varchar(30), text varchar(2000), article_url varchar(100),
  topics varchar(200), at_users varchar(1000), pics varchar(3000),
  video_url varchar(1000), live_photo_url varchar(1000), location varchar(100),
  created_at DATETIME, source varchar(30), attitudes_count INT, comments_count INT,
  reposts_count INT, retweet_id varchar(20), edited BOOLEAN DEFAULT 0,
  edit_count INT DEFAULT 0, retweet_text TEXT DEFAULT '',
  location_url varchar(300) DEFAULT '', region varchar(50) DEFAULT '',
  PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS bins (
  id integer PRIMARY KEY AUTOINCREMENT, ext varchar(10), data blob,
  weibo_id varchar(20), comment_id varchar(20), path text, url text);
CREATE TABLE IF NOT EXISTS comments (
  id varchar(20) NOT NULL, bid varchar(20) NOT NULL, weibo_id varchar(32) NOT NULL,
  root_id varchar(20), user_id varchar(20) NOT NULL, created_at varchar(20),
  user_screen_name varchar(64) NOT NULL, user_avatar_url text, text varchar(1000),
  pic_url text, like_count integer, ip_location varchar(50) DEFAULT '',
  PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS reposts (
  id varchar(20) NOT NULL, bid varchar(20) NOT NULL, weibo_id varchar(32) NOT NULL,
  user_id varchar(20) NOT NULL, created_at varchar(20),
  user_screen_name varchar(64) NOT NULL, user_avatar_url text, text varchar(1000),
  like_count integer, PRIMARY KEY (id));
CREATE INDEX IF NOT EXISTS idx_weibo_user_time ON weibo (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comments_weibo ON comments (weibo_id);
CREATE INDEX IF NOT EXISTS idx_reposts_weibo ON reposts (weibo_id);
"""

TEXTS = [
    "今天天气不错，出来走走。",
    "终于把这个功能写完了，记录一下。",
    "转发一条有意思的微博，顺便说两句。",
    "中午吃了碗热干面，还是老味道。",
    "整理相册翻到三年前的照片，时间真快。",
    "新买的键盘手感不错，打字都变快了。",
    "看完这本书，推荐给还在犹豫的人。",
    "下雨了，窗外的声音很好听。",
    "试着用新方法做了一次备份，成功。",
    "周末去了趟东湖，人不少。",
]


def main():
    sys.path.insert(0, ROOT)
    os.environ.setdefault("WEIBO_DATA_DIR", os.path.join(ROOT, "data"))
    from weibo_reader.paths import DATA_DIR as DD, DB_PATH, EMOJI_DIR  # noqa

    try:
        from PIL import Image, ImageDraw
        has_pil = True
    except Exception:
        has_pil = False

    if os.path.isfile(DB_PATH):
        print("已存在 %s，先备份/删除再跑" % DB_PATH)
        return
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)

    uid, nick = "1000000001", "示例用户"
    con.execute("INSERT OR REPLACE INTO user (id, nick_name, gender, location, ip_location,"
                " bio, follower_count, follow_count) VALUES (?,?,?,?,?,?,?,?)",
                (uid, nick, "f", "湖北", "湖北", "这是一个演示账号", 123, 45))

    img_dir = os.path.join(DD, "img", nick)
    os.makedirs(img_dir, exist_ok=True)

    base = time.time() - 86400 * 40
    wid_of = []
    for i in range(20):
        wid = str(5000000000000000 + i)
        wid_of.append(wid)
        created = time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(base + i * 86400 * 2))
        pics = []
        if i % 3 == 0:
            stamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.strptime(created, "%Y-%m-%d %H:%M:%S"))
            n = 1 if i % 6 == 0 else 3
            for k in range(1, n + 1):
                fn = "%s_%d.png" % (stamp, k) if n > 1 else "%s.png" % stamp
                pics.append(fn)
                if has_pil:
                    w, h = (900, 240) if k == 1 and n == 1 else (400, 400)
                    im = Image.new("RGB", (w, h), (random.randint(60, 140),
                                                   random.randint(90, 160),
                                                   random.randint(140, 210)))
                    d = ImageDraw.Draw(im)
                    d.text((16, h // 2 - 8), "demo image %d-%d" % (i, k), fill="white")
                    im.save(os.path.join(img_dir, fn))
        con.execute(
            "INSERT INTO weibo (id, bid, user_id, screen_name, text, pics, location,"
            " created_at, source, attitudes_count, comments_count, reposts_count,"
            " retweet_id, region) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (wid, "B" + str(i), uid, nick, TEXTS[i % len(TEXTS)],
             ",".join(pics), "", created,
             random.choice(["iPhone 15", "微博网页版", "Android"]),
             random.randint(0, 300), 0, 0, "", "湖北"))

    # 一条转发 + 原帖
    orig = str(5000000000000900)
    con.execute(
        "INSERT INTO weibo (id, bid, user_id, screen_name, text, created_at, source,"
        " attitudes_count, comments_count, reposts_count) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (orig, "ORIG", "1000000002", "被转发的博主", "这是一条被转发的原帖，用来演示原帖块。",
         time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + 3600)), "iPhone 15", 12, 0, 0))
    con.execute(
        "INSERT INTO weibo (id, bid, user_id, screen_name, text, created_at, source,"
        " attitudes_count, retweet_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (str(5000000000000901), "RT1", uid, nick, "转发理由写在这里。",
         time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + 7200)), "微博网页版", 1, orig))

    # 评论
    for i in range(6):
        con.execute(
            "INSERT INTO comments (id, bid, weibo_id, user_id, created_at, user_screen_name,"
            " text, like_count, ip_location) VALUES (?,?,?,?,?,?,?,?,?)",
            (str(6000000000000000 + i), "C%d" % i, wid_of[i], "1000000003",
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + i * 600)),
             "路过的网友%d" % i, "评论示例 %d" % i, i * 3, "湖北"))
    con.commit()
    con.close()

    # 表情：如果 data/emoji 是空的，给几个占位
    if not os.listdir(EMOJI_DIR) and has_pil:
        from PIL import Image
        for name in ("微笑", "可爱", "doge", "吃瓜"):
            Image.new("RGB", (24, 24), (250, 210, 120)).save(
                os.path.join(EMOJI_DIR, name + ".png"))

    print("demo 库已生成：%s" % DB_PATH)
    print("现在运行：python run.py")


if __name__ == "__main__":
    main()
