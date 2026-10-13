"""
controllers 包：控制层的主要模块及功能模块的集合（主要是Tornado RequestHandler）
所有的控制器都继承BaseHandler，这里有三个通用能力，避免每个Handler都重复实现：
1、从签名cookie中获取用户信息，放到self.current_user中
Tornado的@tornado.web.authenticated装饰器会检查self.current_user是否为None，如果为None则返回403
2、write_json：统一的JSON响应方法输出数据（含中文不转义，固定字符集）
3、sse：把一个事件封装成SSE（Server send events）报文文本
"""
import json
from typing import Optional
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self) -> Optional[str]:
        username = self.get_secure_cookie("username")
        if not username:
            return None
        return username.decode("utf-8")

    def write_json(self, data: dict, status: int=200) -> None:
        """统一的JSON响应方法输出数据（含中文不转义，固定字符集）"""
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        # ensure_ascii=False 不要将中文转义成\uXXXX的形式，保持中文原样输出
        self.write(json.dumps(data, ensure_ascii=False))
        
    @staticmethod
    def sse(event: str, data: dict) -> str:
        """把一个事件封装成SSE (Server send events) 报文文本"""
        sse_data = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {sse_data}\n\n"