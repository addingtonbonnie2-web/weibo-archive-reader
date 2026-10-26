# -*- coding: utf-8 -*-
"""生成一个不含真实数据的 demo 库：一年半的假微博 + 图片 + 评论 + 收藏 + 标签

用法（在仓库根目录执行）：
    python tools/make_demo_db.py

会创建 data/weibo.db、data/<昵称>/img/ 下的示例图片，之后 python run.py 就能看界面。
"""
import os
import random
import sqlite3
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
    "中午吃了碗热干面，还是老味道。",
    "整理相册翻到三年前的照片，时间真快。",
    "新买的键盘手感不错，打字都变快了。",
    "看完这本书，推荐给还在犹豫的人。",
    "下雨了，窗外的声音很好听。",
    "试着用新方法做了一次备份，成功。",
    "周末去了趟东湖，人不少。",
    "把阳台的花搬到窗边，光照好一些。",
    "凌晨两点的街道，比白天安静太多。",
    "把旧手机里的照片导出来了，一千多张。",
    "这周第三次加班，决定明天早点睡。",
    "楼下的猫又来了，蹲在台阶上晒太阳。",
    "随手拍的路牌，颜色挺好看。",
]
TOPICS = ["#日常#", "#随手拍#", "#读书笔记#", "#吃点什么#", "#加班日记#"]


def main():
    os.environ.setdefault("WEIBO_DATA_DIR", os.path.join(ROOT, "data"))
    from weibo_reader.paths import DATA_DIR as DD, DB_PATH, EMOJI_DIR  # noqa

    try:
        from PIL import Image, ImageDraw
        has_pil = True
    except Exception:
        has_pil = False

    if os.path.isfile(DB_PATH):
        print("已存在 %s，先删除再跑" % DB_PATH)
        return

    random.seed(20260101)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)

    uid, nick = "1000000001", "示例用户"
    con.execute("INSERT OR REPLACE INTO user (id, nick_name, gender, location, ip_location,"
                " bio, follower_count, follow_count) VALUES (?,?,?,?,?,?,?,?)",
                (uid, nick, "f", "湖北", "湖北", "演示用账号，全部是假数据", 128, 96))

    # 目录布局要和阅读器一致：<数据目录>/<昵称>/img/、<数据目录>/<昵称>/avatar.png
    account_dir = os.path.join(DD, nick)
    img_dir = os.path.join(account_dir, "img")
    os.makedirs(img_dir, exist_ok=True)

    def shot(path, w, h, color, label):
        if not has_pil:
            return
        im = Image.new("RGB", (w, h), color)
        d = ImageDraw.Draw(im)
        d.rectangle([4, 4, w - 5, h - 5], outline=(255, 255, 255), width=3)
        if label:
            d.text((18, h // 2 - 6), label, fill=(255, 255, 255))
        im.save(path)

    if has_pil:
        shot(os.path.join(account_dir, "avatar.png"), 120, 120,
             (120, 90, 160), "DEMO")

    base = time.time() - 86400 * 500
    ids = []
    n_posts = 60
    for i in range(n_posts):
        wid = str(5100000000000000 + i)
        ids.append(wid)
        created = time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(base + i * 86400 * 8 + random.randint(0, 40000)))
        stamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.strptime(created, "%Y-%m-%d %H:%M:%S"))
        pics = []
        if i % 3 == 0:
            cnt = 1 if i % 9 == 0 else 3
            for k in range(1, cnt + 1):
                fn = ("%s_%d.png" % (stamp, k)) if cnt > 1 else ("%s.png" % stamp)
                pics.append(fn)
                w, h = (900, 260) if cnt == 1 else (420, 420)
                shot(os.path.join(img_dir, fn), w, h,
                     (random.randint(70, 130), random.randint(100, 160),
                      random.randint(150, 210)), "demo %d-%d" % (i, k))
        text = TEXTS[i % len(TEXTS)]
        if i % 4 == 0:
            text = TOPICS[i % len(TOPICS)] + " " + text
        con.execute(
            "INSERT INTO weibo (id, bid, user_id, screen_name, text, pics, location,"
            " created_at, source, attitudes_count, comments_count, reposts_count,"
            " retweet_id, region) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (wid, "B" + str(i), uid, nick, text, ",".join(pics), "",
             created, random.choice(["iPhone 15", "微博网页版", "Android", "iPad Air"]),
             random.randint(0, 420), 0, 0, "", "湖北"))

    originals = [
        ("被转发的博主甲", "这是一条被转发的原帖，用来演示原帖块的样子。"),
        ("被转发的博主乙", "另一条原帖内容，带话题 #示例话题#，用于展示引用排版。"),
    ]
    for j, (onick, otext) in enumerate(originals):
        oid = str(5100000000009000 + j)
        con.execute(
            "INSERT INTO weibo (id, bid, user_id, screen_name, text, created_at, source,"
            " attitudes_count, comments_count, reposts_count) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (oid, "O%d" % j, "1000000009", onick, otext,
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + j * 900)), "iPhone 15",
             12 + j, 3, 7))
        con.execute(
            "INSERT INTO weibo (id, bid, user_id, screen_name, text, created_at, source,"
            " attitudes_count, retweet_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (str(5100000000009100 + j), "R%d" % j, uid, nick,
             ["今天看到这条，顺手记一下。", "这个说法有意思。"][j],
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + j * 900 + 600)),
             "微博网页版", 1, oid))

    for i in range(12):
        con.execute(
            "INSERT INTO comments (id, bid, weibo_id, user_id, created_at, user_screen_name,"
            " text, like_count, ip_location) VALUES (?,?,?,?,?,?,?,?,?)",
            (str(6100000000000000 + i), "C%d" % i, ids[i],
             "1000000003", time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(base + i * 3600)),
             "路过的网友%d" % (i % 4), "评论示例 %d：这条不错。" % i,
             random.randint(0, 40), random.choice(["湖北", "北京", "广东", "上海"])))

    con.execute("""CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_uid varchar(20), author_nick varchar(50),
      author_uid varchar(20), weibo_id varchar(20), time varchar(30), text TEXT,
      imgs TEXT, tag varchar(50) DEFAULT '')""")
    for j, (an, at) in enumerate([("被转发的博主甲", "收藏的示例内容一，留着自己回看。"),
                                  ("被转发的博主乙", "收藏的示例内容二。")]):
        con.execute("INSERT INTO favorites (owner_uid, author_nick, author_uid, weibo_id,"
                    " time, text, imgs, tag) VALUES (?,?,?,?,?,?,?,?)",
                    (uid, an, "1000000009", str(5100000000009000 + j),
                     time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(base + 86400)),
                     at, "", "示例合集"))

    con.execute("""CREATE TABLE IF NOT EXISTS weibo_tags (
      id INTEGER PRIMARY KEY AUTOINCREMENT, weibo_id varchar(20), tag varchar(50),
      created_at varchar(30))""")
    for i, tag in ((0, "好吃的"), (3, "好吃的"), (5, "读书"), (9, "好吃的"), (12, "加班")):
        con.execute("INSERT INTO weibo_tags (weibo_id, tag, created_at) VALUES (?,?,?)",
                    (ids[i], tag, time.strftime("%Y-%m-%d %H:%M:%S")))

    con.commit()
    con.close()

    if not os.listdir(EMOJI_DIR) and has_pil:
        for name in ("微笑", "可爱", "doge", "吃瓜"):
            shot(os.path.join(EMOJI_DIR, name + ".png"), 24, 24, (250, 210, 120), "")

    print("demo 库已生成：%s" % DB_PATH)
    print("共 %d 条微博 + 2 条转发 + 12 条评论 + 2 条收藏 + 5 个标签" % n_posts)
    print("现在运行：python run.py")


if __name__ == "__main__":
    main()
