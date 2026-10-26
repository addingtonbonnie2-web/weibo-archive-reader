# -*- coding: utf-8 -*-
"""微博归档阅读器 · 启动入口

    python run.py

配置见仓库根目录的 config.py（不存在时用默认值）。
"""
import os
import socket
import sys

from weibo_reader.core import app, get_conf
from weibo_reader.paths import DATA_DIR, DB_PATH
from weibo_reader import routes  # noqa: F401  注册所有路由


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


def main():
    host = get_conf("HOST", "127.0.0.1")
    port = int(get_conf("PORT", 5055))
    code = get_conf("ACCESS_CODE", "")

    print("=" * 56)
    print(" 微博归档阅读器")
    print("=" * 56)
    print(" 本机访问 : http://127.0.0.1:%d" % port)
    if host == "0.0.0.0":
        ip = lan_ip()
        if ip:
            print(" 局域网   : http://%s:%d  （手机连同一 WiFi 可打开）" % (ip, port))
        print(" 访问口令 : %s" % ("已设置" if code else "未设置（同一局域网内谁都能看）"))
    else:
        print(" 局域网   : 未开启（config.py 里 HOST 改成 0.0.0.0 可开启）")
    print(" 数据目录 : %s" % DATA_DIR)
    if not os.path.isfile(DB_PATH):
        print(" ⚠ 还没找到 weibo.db，先跑 python tools/make_demo_db.py 看示例")
    print("=" * 56)

    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
