# -*- coding: utf-8 -*-
"""路径解析：所有目录都在这里决定，其它模块只引用，不自己拼路径。

优先级：
  1. 环境变量 WEIBO_DATA_DIR
  2. 仓库根目录 config.py 里的 DATA_DIR
  3. 默认 <仓库根>/data
"""
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PY = os.path.join(APP_DIR, "config.py")
STATIC_DIR = os.path.join(APP_DIR, "static")


def _config_data_dir():
    """从 config.py 里读 DATA_DIR（读不到就返回空）"""
    if not os.path.isfile(CONFIG_PY):
        return ""
    try:
        ns = {}
        with open(CONFIG_PY, encoding="utf-8-sig") as f:
            exec(compile(f.read(), CONFIG_PY, "exec"), ns)
        return str(ns.get("DATA_DIR") or "")
    except Exception:
        return ""


DATA_DIR = (os.environ.get("WEIBO_DATA_DIR")
            or _config_data_dir()
            or os.path.join(APP_DIR, "data"))

DB_PATH = os.path.join(DATA_DIR, "weibo.db")
EMOJI_DIR = os.path.join(DATA_DIR, "emoji")
BG_DIR = os.path.join(DATA_DIR, "bg")
FONTS_JSON = os.path.join(DATA_DIR, "fonts.json")
ANNOT_DIR = os.path.join(DATA_DIR, "annotations")

for _d in (DATA_DIR, EMOJI_DIR, BG_DIR, ANNOT_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass
