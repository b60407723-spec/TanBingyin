import os
import tornado.web
import tornado.ioloop
from app.application import make_app

def main() -> None:
    port = 10086
    webapp = make_app()
    webapp.listen(port)
    print(f"Server Run @ http://localhost:{port}/")
    print("Ctrl + C 停止服务")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()