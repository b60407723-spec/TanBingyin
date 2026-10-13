"""
Agentica 智能体服务（Service 层）
职责：按登录用户组装并缓存Agent，向上层提供：
- stream_answer(message,user_id)：异步生成器，逐块产生SSE事件Dict
- get_agent(user_id)：拿到该用户的Agent(首次创建，之后复用)

为什么单独成层：
- tornado的Handler只关心http不关心大模型/工具细节
- agent比较重（要加载工具，记忆），按user_id缓存可以避免每个请求重建
- workspace 用 user_id 隔离，不同用户的长期记忆互不串号
"""
import os
from pathlib import Path
from typing import AsyncIterator,Dict,List
from dotenv import load_dotenv
from agentica import (
    Agent,
    OpenAIChat,
    Workspace,
    WeatherTool,
    BuiltinTodoTool,
    BuiltinTaskTool,
    BuiltinMemoryTool,
    BuiltinWebSearchTool,
    RunEvent
)

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_WORKSPACE_DIR = _BASE_DIR / "workspace"

#{user_id:Agent}
_agents: Dict[str,Agent]={}

def _require_env(name: str) -> str:
    """读取必需的环境变量；缺失时给出明确提示，引导使用者自备 .env。"""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"缺少环境变量 {name}：请复制 .env.example 为 .env，"
            "填写 OPENAI_BASE_URL / OPENAI_API_KEY / MODEL_ID 三项配置后重启服务。"
        )
    return value

def build_agent(user_id:str) -> Agent:
    model = OpenAIChat(
        id=_require_env("MODEL_ID"),
        api_key=_require_env("OPENAI_API_KEY"),
        base_url=_require_env("OPENAI_BASE_URL")
    )
    return Agent(
        model=model,
        name="旅行规划师",
        instructions=[
            "你是一位资深的旅游规划师，服务同一个用户。",
            "复杂请求先用 builtin_todo_tool 拆解任务清单，再逐项完成。",
            "需要独立调研（如天气、景点、美食、交通）时，用builtin_task_tool 并行派出多个子智能体。",
            "每个子智能体负责一个主题，最后由你汇总。",
            "查询目的地天气用 weather 工具。",
            "主动记住用户的出行偏好（如饮食习惯、忌口、预算、出行节奏、是否照顾老人小孩），下次规划时直接复用记忆功能。",
            "输入用条理清晰的 Markdown。",
        ],
        tools=[
            WeatherTool(),
            BuiltinTodoTool(),
            BuiltinTaskTool(),
            BuiltinMemoryTool(),
            BuiltinWebSearchTool()
        ],
        workspace=Workspace(str(_WORKSPACE_DIR),user_id=user_id),
        enable_long_term_memory=True,
        enable_experience_capture=True
    )
    
def get_agent(user_id:str = "travel-user") -> Agent:
    if user_id not in _agents:
        _agents[user_id] = build_agent(user_id)
    return _agents[user_id]

async def stream_answer(message:str,user_id:str = "travel-user") -> AsyncIterator[Dict]:
    agent = get_agent(user_id)
    answer_parts: List[str] = []
    async for resp in agent.run_stream(message):
        # 工具调用事件：转发工具名与参数（字段为 tool_name / tool_args）
        if resp.event == RunEvent.tool_call_started:
            tool_call = resp.tool_call
            if tool_call is not None:
                yield {
                    "type":"tool",
                    "name":tool_call.tool_name,
                    "arguments":tool_call.tool_args,
                }
            continue
        # 只处理增量响应事件；跳过收尾的 run_completed（其 content 为聚合后的完整内容，会导致重复）
        if resp.event != RunEvent.run_response:
            continue
        # 推理增量的 content 为 None，需独立转发
        if resp.reasoning_content:
            yield {"type":"reasoning","text":resp.reasoning_content}
        # 正文增量
        if resp.content:
            answer_parts.append(resp.content)
            yield {"type":"delta","text":resp.content}
    # 循环结束后统一发送一次 done，携带完整回答
    yield {"type":"done","text":"".join(answer_parts)}