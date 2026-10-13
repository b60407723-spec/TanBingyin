"""
对话相关的的Controller

包含两个接口，都需要登录：
• ChatHandler：POST /api/chat，以SSE流式响应返回智能体问答。
• HistoryHandler：GET /api/history，返回当前用户在SQLITE中的最近对话。

与页面接口的区别：页面用@authenticated未登录时302跳转。
这里是给前端fetch用的数据接口，未登录统一返回401JSON。
前端判断到401后自行跳转到登录页。
"""
import json
from app.controllers.base import BaseHandler
from app.models.message import MessageRepository
from app.services.agent_service import stream_answer

class ChatHandler(BaseHandler):
    async def post(self) -> None:
        if not self.current_user:
            self.write_json({"detail":"未登录","login_url":"/auth/login"},status=401)
            return
        try:
            payload = json.loads(self.request.body or b"{}")
            message = (payload.get("message") or "").strip()
        except (json.JSONDecodeError,AttributeError):
            self.write_json({"detail":"请求体必须是JSON，且含message字段"},status=400)
            return

        if not message:
            self.write_json({"detail": "Message不能为空"}, status=400)
            return

        username = self.current_user
        MessageRepository.save(username, "user", message)

        self.set_status(200)
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        try:
            async for event in stream_answer(message,user_id=username):
                etype = event["type"]
                if etype=="delta":
                    self.write(self.sse("delta",{"text":event["text"]}))
                elif etype=="tool":
                    self.write(self.sse("tool",{"name":event["name"],"arguments":event["arguments"]}))
                elif etype=="reasoning":
                    self.write(self.sse("reasoning",{"text":event["text"]}))
                elif etype=="done":
                    answer = event.get("text","")
                    if answer:
                        MessageRepository.save(username,"assistant",answer)
                    self.write(self.sse("done",{}))
                await self.flush()
        except Exception as exc:
            self.write(self.sse("error",{"message":str(exc)}))
            await self.flush()
            
class HistoryHandler(BaseHandler):
    def get(self) -> None:
        if not self.current_user:
            self.write_json({"detail":"未登录","login_url":"/auth/login"},status=401)
            return
        # limit 为非数字时回退默认值，并限制在 1~200，避免异常或超大查询
        try:
            limit = int(self.get_argument("limit","50"))
        except (TypeError,ValueError):
            limit = 50
        limit = max(1,min(limit,200))
        self.write_json({"messages":MessageRepository.list_recent(self.current_user,limit)})