"""
Tornado 应用配置模块
集中完成:
1、路由表（URL模式->Handler类）
2、模板目录、静态文件目录
3、登录/安全相关的配置（cookie_secret、login_url、XSRF）
4、启动前调用init_db()确保数据表存在

make_app() 返回一个tornado.web.Application，由根目录app.py负责listen和启动事件循环
"""
import os
import tornado.web
from app.controllers.auth import LoginHandler, LogoutHandler, RegisterHandler
from app.controllers.chat import ChatHandler,HistoryHandler
from app.controllers.page import HealthHandler, IndexHandler
from app.models.db import init_db

_BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
TEMPLATE_DIR = os.path.join(_BASE_DIR, "app", "templates")
STATIC_DIR = os.path.join(_BASE_DIR, "app", "static")

def make_app() -> tornado.web.Application:
    init_db()
    return tornado.web.Application(
        [
            (r"/",IndexHandler),
            (r"/auth/login",LoginHandler),
            (r'/auth/logout',LogoutHandler),
            (r'/auth/register',RegisterHandler),
            (r"/api/health",HealthHandler),
            (r"/api/chat",ChatHandler),
            (r"/api/history",HistoryHandler),
            (r'/static/(.*)',tornado.web.StaticFileHandler,{"path":STATIC_DIR})
        ],
        template_path=TEMPLATE_DIR,
        static_path=STATIC_DIR,
        cookie_secret="agentica-demo-secret",
        login_url="/auth/login",
        xsrf_cookies=True,
        debug=True
    )