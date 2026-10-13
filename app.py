"""
服务入口：组装 Tornado Application，绑定端口并启动事件循环。

运行：python app.py
若端口已被占用，会给出明确的中文提示并退出，而不是抛出异常堆栈。
"""
import sys

import tornado.ioloop
import tornado.web

from app.application import make_app

PORT = 10086

def main() -> None:
    port = PORT
    webapp = make_app()
    try:
        webapp.listen(port)
    except OSError:
        # 端口被占用时（Windows 报 WinError 10048），给出可操作的提示而非堆栈
        print(f"启动失败：端口 {port} 已被占用。")
        print("请先停止已运行的实例（或结束占用该端口的进程），再重新运行本服务。")
        sys.exit(1)
    print(f"Server Run @ http://localhost:{port}/")
    print("Ctrl + C 停止服务")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
