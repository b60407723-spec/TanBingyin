"""
页面与健康检查相关的Handler
- IndexHandler：渲染登录后才能看以的聊天主界面
- HealthHandler：返回模型 / Key / 工具等运行配置，供前端和排查使用
"""
import os
import tornado.web
from app.controllers.base import BaseHandler

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        """渲染登录后才能看以的聊天主界面"""
        self.render("index.html", title="多智能体规划工作台", username=self.current_user)
        
class HealthHandler(BaseHandler):
    def get(self):
        """返回模型 / Key / 工具等运行配置，供前端和排查使用"""
        health_info = {
            "model": os.environ.get("MODEL_ID", "deepseek-chat"),
            "api_key": "已配置" if os.environ.get("OPENAI_API_KEY") else "未配置",
        }
        self.write_json(health_info)