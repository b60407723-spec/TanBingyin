# 项目架构说明

> 说明对象：`tbyAgenticBaseWeb` —— 基于 **Tornado + Agentica + SQLite** 的智能体工作台 Web 服务。
> 本文件由 AI 依据现有代码整理而成，作为后续开发者的架构基线。

---

## 1. 项目定位

一个 **MVC 分层** 的 Python Web 服务，目标是承载「多智能体规划工作台」：
- 提供用户体系（注册 / 登录 / 登出）作为入口门槛；
- 前端以登录页作为落地页，登录后进入主工作台；
- 后端已接入 **Agentica** 智能体编排，打通「提问 → 智能体流式回答（SSE）→ 消息落库 → 历史回显」最小闭环。

现有代码已经完成：
- **框架层**：Tornado 应用工厂、路由表、静态资源、模板目录、XSRF、Cookie 认证；
- **数据层**：SQLite 连接工厂、`users` / `messages` 表初始化、`UserRepository` 密码哈希仓储、`MessageRepository` 对话仓储；
- **服务层**：`app/services/agent_service.py` —— 按登录用户组装并缓存 Agentica `Agent`，提供 SSE 流式回答；
- **控制层**：登录 / 注册 / 登出 / 首页 / 健康检查，以及对话 `ChatHandler`、历史 `HistoryHandler`；
- **模板层**：`base.html` + `login.html` + `index.html`；
- **测试**：`test/test_user.py` 覆盖注册 + 校验；
- **视觉稿**：`dist/登录页面.html` 提供高保真前端原型（Tailwind + FontAwesome）。

---

## 2. 目录结构

```
tbyAgenticBaseWeb/
├── app.py                          # 服务入口，监听 10086 端口
├── .env                            # 模型端点配置（OPENAI_BASE_URL / API_KEY / MODEL_ID）
├── database/
│   └── app.db                      # SQLite 数据库文件（运行时生成）
├── app/
│   ├── __init__.py                 # 包说明：MVC 分层职责
│   ├── application.py              # Tornado Application 工厂 make_app()
│   ├── controllers/                # 控制层：RequestHandler
│   │   ├── __init__.py
│   │   ├── base.py                 #   BaseHandler：get_current_user / write_json / sse
│   │   ├── auth.py                 #   Login / Register / Logout
│   │   ├── page.py                 #   Index / Health
│   │   └── chat.py                 #   Chat / History：SSE 问答 + 历史查询
│   ├── models/                     # 数据层：Repository 模式
│   │   ├── __init__.py
│   │   ├── db.py                   #   SQLite 连接工厂 + init_db() 建表
│   │   ├── user.py                 #   UserRepository：注册 / 校验 / 按用户名查询
│   │   └── message.py              #   MessageRepository：对话落库 / 近 N 条查询
│   ├── services/                   # 服务层：Agentica 智能体编排
│   │   ├── __init__.py
│   │   └── agent_service.py        #   build_agent / get_agent / stream_answer
│   ├── static/                     # 以下三个文件当前均为空（占位）
│   │   ├── css/style.css
│   │   ├── js/app.js
│   │   └── js/login.js
│   └── templates/
│       ├── base.html               # 母版：head + block body / scripts
│       ├── login.html              # 登录页
│       ├── register.html           # 占位，未填充
│       └── index.html              # 登录后主界面（侧边栏 + 对话区工作台）
├── test/
│   └── test_user.py                # 用户注册 / 校验的脚本级测试
├── dist/
│   ├── 登录页面.html                 # 高保真登录页视觉原型（Tailwind）
│   └── 后台首页.html                 # 高保真主工作台视觉原型（Tailwind，index.html 的来源）
└── docx/                           # 项目文档
    ├── agent-rules.md              # 协作与流程规则
    ├── architecture.md             # 本文件
    ├── changelog.md                # 变更历史
    └── requirements.md             # 需求与验收标准
```

---

## 3. 分层职责（MVC）

| 层 | 目录 | 职责 | 关键类 / 函数 |
| --- | --- | --- | --- |
| 入口 | 根 `app.py` | 组装 Application、绑定端口、启动事件循环 | `main()` |
| 应用工厂 | `app/application.py` | 路由表、模板目录、静态目录、安全配置、启动前建表 | `make_app()` |
| 控制层 | `app/controllers/` | HTTP 请求 → 视图渲染 / JSON / SSE；不直接写 SQL | `BaseHandler`、`LoginHandler`、`RegisterHandler`、`LogoutHandler`、`IndexHandler`、`HealthHandler`、`ChatHandler`、`HistoryHandler` |
| 数据层 | `app/models/` | 表结构、连接工厂、密码哈希、SQL 封装 | `init_db`、`get_connetcion`、`UserRepository`、`MessageRepository` |
| 服务层 | `app/services/` | 智能体组装 / 缓存 / 调度（**唯一引用 `agentica` 的层**） | `build_agent`、`get_agent`、`stream_answer` |
| 视图层 | `app/templates/` | HTML 模板，继承 `base.html` | `base.html`、`login.html`、`index.html` |
| 静态资源 | `app/static/` | CSS / JS，`/static/*` 由 `StaticFileHandler` 服务 | `css/style.css`、`js/app.js` |

**分层约束**：
- Controller **不得** 直接写 SQL，必须经 `models/*.py` 中的 `*Repository`；
- Service 是唯一允许引用 `agentica` 包的层（避免把智能体逻辑泄漏到控制器）；
- Model 层不引用 `tornado`（保持可单测、可替换存储引擎）；
- 模板只读 Controller 传入的上下文，不承担业务判断。

---

## 4. 启动流程

```
python app.py
    │
    ▼
make_app()                         # app/application.py
    │
    ├── init_db()                  # 创建 database/ 与 app.db；CREATE TABLE users / messages
    ├── tornado.web.Application(
    │       [
    │           (r"/",               IndexHandler),
    │           (r"/auth/login",     LoginHandler),
    │           (r"/auth/logout",    LogoutHandler),
    │           (r"/auth/register",  RegisterHandler),
    │           (r"/api/health",     HealthHandler),
    │           (r"/api/chat",       ChatHandler),
    │           (r"/api/history",    HistoryHandler),
    │           (r"/static/(.*)",    StaticFileHandler, {"path": STATIC_DIR}),
    │       ],
    │       template_path=app/templates,
    │       static_path=app/static,
    │       cookie_secret="agentica-demo-secret",
    │       login_url="/auth/login",
    │       xsrf_cookies=True,
    │       debug=True
    │   )
    │
    ▼
webapp.listen(10086)
IOLoop.current().start()
```

> **注意**：`.env` 由 `app/services/agent_service.py` 顶部的 `load_dotenv()` 在 Service 层加载；
> `app.py` / `make_app()` 本身**未**加载 `.env`。`HealthHandler` 仍通过 `os.environ.get(...)` 读取
> `MODEL_ID` / `OPENAI_API_KEY`，依赖上游（Service 层加载或外部注入）。

---

## 5. 路由清单

| 方法 | 路径 | Handler | 是否需登录 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/` | `IndexHandler` | 是（`@authenticated`） | 渲染主工作台页面 |
| GET/POST | `/auth/login` | `LoginHandler` | 否 | 展示登录页 / 校验并写 Cookie |
| GET/POST | `/auth/register` | `RegisterHandler` | 否 | 展示注册页 / 创建用户（模板 `register.html` 仍为空） |
| POST | `/auth/logout` | `LogoutHandler` | 否 | 清 Cookie 后跳转登录 |
| GET | `/api/health` | `HealthHandler` | 否 | 报告 MODEL_ID / API_KEY 配置状态（**实现未完成，见 §11**） |
| POST | `/api/chat` | `ChatHandler` | 是（自检，未登录返回 401 JSON） | 接收 `{message}`，以 SSE 流式返回智能体回答，并落库 |
| GET | `/api/history` | `HistoryHandler` | 是（自检，未登录返回 401 JSON） | 返回当前用户最近 `limit` 条对话（默认 50） |
| GET | `/static/(.*)` | `StaticFileHandler` | 否 | 静态资源 |

> 页面类接口用 `@authenticated`（未登录 302 跳登录页）；数据类接口（`/api/*`）自行判断
> `self.current_user`，未登录统一返回 `401 JSON` + `login_url`，由前端 `fetch` 捕获后跳转。

---

## 6. 数据层

### 6.1 存储

- 引擎：**SQLite**（`sqlite3` 标准库，未引入 SQLAlchemy）
- 文件：`database/app.db`，路径由 `app.models.db._project_root()` 计算
- 连接工厂：`get_connetcion()`，`row_factory = sqlite3.Row`（结果可按列名访问）
- 初始化：`init_db()` 在 `make_app()` 之前调用，幂等建表

### 6.2 表结构

`users`
```sql
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
```

`messages`
```sql
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL DEFAULT '',
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
```

### 6.3 密码策略

- 算法：**PBKDF2-HMAC-SHA256**，迭代次数 `100_000`（`UserRepository._PBKDF2_ITERATIONS`）
- 盐：**随机 16 字节**，`secrets.token_bytes(16)`，随用户一起落库（hex 存储）
- 比对：登录时用同 salt 重新哈希，`==` 直接字符串比对（**非恒定时间**，安全性弱于 `hmac.compare_digest`）
- 明文密码：不入库、不写日志

### 6.4 Repository 模式

- 一个表 → 一个 `*Repository`，静态方法聚合 SQL；
- Controller 只 `import` `UserRepository`，不 `import sqlite3`；
- 未来扩展 `MessageRepository` / `SessionRepository` 时应沿用同构风格。

---

## 7. 会话与认证

- 凭据：`set_secure_cookie("username", username)`（Tornado 签名 Cookie，非 JWT）
- 校验：`BaseHandler.get_current_user()` 解签，无 Cookie 返回 `None`
- 保护：`@tornado.web.authenticated` 装饰器；返回 `None` 时框架自动跳 `login_url`
- 清理：`clear_cookie("username")`
- 表单防 CSRF：所有 `method="post"` 表单必须包含 `{% module xsrf_form_html() %}`

---

## 8. 安全基线

- 启用 `xsrf_cookies=True`；
- Cookie 使用 `set_secure_cookie` / `get_secure_cookie`（签名防篡改）；
- 密码不落明文，独立 salt；
- `login_url` 显式指向 `/auth/login`；
- `debug=True` **仅限本地开发**，生产需置 `False` 并替换 `cookie_secret`。

已知缺口：
- `cookie_secret` 硬编码为 `"agentica-demo-secret"`，生产必须外置；
- PBKDF2 结果直接 `==` 比对，理论上存在时序侧信道；
- `HealthHandler` 会暴露 KEY 是否配置的状态，生产应删除或加鉴权。

---

## 9. Agentica 集成（已接入）

智能体逻辑集中在 [`app/services/agent_service.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/services/agent_service.py)，对外只暴露三个函数：

- `build_agent(user_id)`：用 `OpenAIChat`（读取 `.env` 的 `MODEL_ID` / `OPENAI_API_KEY` / `OPENAI_BASE_URL`）
  构造一个名为「旅行规划师」的 `Agent`，装载工具 `WeatherTool`、`BuiltinTodoTool`、`BuiltinTaskTool`、
  `BuiltinMemoryTool`、`BuiltinWebSearchTool`；`workspace` 以 `user_id` 隔离，开启长期记忆与经验捕获。
- `get_agent(user_id)`：按 `user_id` 缓存 `Agent`（首次创建，之后复用，避免每请求重建）。
- `stream_answer(message, user_id)`：异步生成器，`agent.run_stream()` 逐块产出事件字典
  （`delta` 文本 / `tool` 调用 / `reasoning` 推理 / `done` 汇总），供 Controller 转成 SSE。

项目内 `.venv/Lib/site-packages/agentica` 已安装，可用能力包括：
- `Agent` / `DeepAgent`：智能体核心
- `OpenAIChat` 及一批 OpenAI 兼容厂商工厂（DeepSeek / Moonshot / Ark / Qwen / ZhipuAI / OpenRouter 等）
- `Builtin*Tool`：文件、执行、抓取、搜索、TODO、任务、记忆、Web
- `Workflow` / `Hooks` / `Memory` / `Checkpoint` / `Critic` / `Experience`
- `SqliteDb` / `RedisDb` / `MysqlDb` / `InMemoryDb` / `JsonDb`
- `Knowledge` / `VectorDb` / `Embedding` / `Rerank`（可选 extras）
- `MCPClient` / `ACPServer` / `Gateway`（可选 extras）

集成约束：
1. Agentica 相关 import 只允许出现在 `app/services/` 及 `app/models/`（数据库侧）；
2. LLM 调用通过 `.env` 中的 `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `MODEL_ID` 注入；
3. 对话流输出统一走 `BaseHandler.sse()` 打包为 SSE 事件；
4. 对话入库统一走 `messages` 表，`role ∈ {user, assistant, system, tool}`。

### 9.1 对话数据流（已实现）

```
浏览器 index.html
  │  POST /api/chat  {message}   Header: X-XSRFToken
  ▼
ChatHandler.post  ── 未登录→401 JSON ── 保存 user 消息(MessageRepository.save)
  │  Content-Type: text/event-stream
  ▼
stream_answer(message, user_id=username)   ← agent_service（按用户缓存的 Agent）
  │  Agentica run_stream 逐块产出
  ▼  agent_service  │  ChatHandler 转 SSE 帧
  delta       → event: delta      data:{"text":..}
  tool        → event: tool       data:{"name":..,"arguments":..}
  reasoning   → event: reasoning  data:{"text":..}
  done        → event: done       data:{}   + 保存 assistant 消息
  ▼
前端 ReadableStream 逐帧解析，增量刷新气泡
```

---

## 10. 前端约束

- 模板基于 **Tornado 内置模板引擎**（`{% extends %}`、`{% block %}`、`{% module %}`），**不要** 引入 Jinja2 / 前端框架；
- 静态资源放在 `app/static/css`、`app/static/js`，通过 `/static/<子路径>` 引用；
- 登录 / 登出 / 注册等表单必须包含 `{% module xsrf_form_html() %}`；
- 高保真视觉稿放在 `dist/` 目录，仅作为设计与交互参考，不参与运行时；
- 当前 `login.html` / `index.html` **经 CDN 引入** Tailwind（`cdn.tailwindcss.com`）与 FontAwesome，与 `requirements.md` NFR-07「静态资源本地化、禁止运行时依赖公共 CDN」存在偏差，属**已知待落地项**；

---

## 11. 当前实现状态总览

| 模块 | 状态 | 备注 |
| --- | --- | --- |
| Tornado 应用工厂 | 完成 | `make_app()` |
| 路由表 | 完成 | 已挂载 `/auth/register`、`/api/health`、`/api/chat`、`/api/history` |
| 认证（登录/登出） | 完成 | Cookie + XSRF |
| 注册 | 完成 | `RegisterHandler` 已实现并挂载 |
| 首页 | 完成 | `@authenticated` |
| 健康检查 | 部分 | `HealthHandler.get()` 构造 `health_info` 后未 `write`（见 §11.1） |
| 用户模型 | 完成 | `UserRepository` |
| 消息模型 | 完成 | `MessageRepository`（`save` / `list_recent` / `count`，`count()` 有缺陷见 §11.1） |
| 服务层 | 完成（存在语法错误） | `agent_service.py` 当前磁盘版本无法编译，见 §11.1 |
| 聊天控制器 | 完成（存在缺陷） | `ChatHandler` / `HistoryHandler`，见 §11.1 |
| 前端问答 | 完成 | `index.html` 已按 `dist/后台首页.html` 原型重写（侧边栏 + 对话区），原 SSE 变量名缺陷已修复（见 §11.1） |
| 静态 CSS / JS | 空 | `style.css` / `app.js` / `login.js` 仅占位 |
| 注册页模板 | 空 | `register.html` 空文件 |
| 测试 | 完成（用户） | `test_user.py`，脚本式 |
| 视觉稿 | 完成 | `dist/登录页面.html` |

### 11.1 当前已知缺陷（学习阶段记录，未修改代码）

> 以下为任务2「学习」阶段对照磁盘代码发现的问题，**仅记录，未做任何修改**，待后续任务确认后处理。

| 文件 | 位置 | 问题 |
| --- | --- | --- |
| `app/services/agent_service.py` | L47（及 L48） | 行尾使用**中文全角逗号** `，`(U+FF0C) → `SyntaxError: invalid character`，**当前文件无法编译** |
| `app/services/agent_service.py` | L61-63 | 列表 `tools=[...]` 的 `]` 与后续参数之间**缺英文逗号** |
| `app/services/agent_service.py` | 缓存声明 | `_agents = Dict[str,Agent]={}` 误将注解写成链式赋值到下标，运行期 `TypeError`，应为 `_agents: Dict[str, Agent] = {}` |
| `app/services/agent_service.py` | `TOOL_NAMES` | 拼写错误 `builtin_task_toll`（且该常量未被使用） |
| `app/services/agent_service.py` | `stream_answer` | `done` 事件的 `yield` 缩进位于 `if resp.content` 内，导致每个文本块都会产出 `done` |
| `app/controllers/chat.py` | `done` 分支 | 用 `event.get("answer","")` 取汇总文本，与 Service 产出的键 `text` 不一致 → assistant 消息永不落库 |
| `app/controllers/chat.py` | `done` 分支 | 拼写错误 `self.lsse(...)`，应为 `self.sse(...)` |
| `app/models/message.py` | `count()` | `if username is None` 分支缺 `return`，`return row["c"]` 缩进落在 `else` 内 |
| `app/controllers/page.py` | `HealthHandler.get()` | 构造 `health_info` 后未 `self.write(...)`，接口无输出 |

> **已修复（任务3）**：`app/templates/index.html` SSE 解析处 `dataline` / `dataLine` 变量名不一致的问题，已随首页原型迭代一并修正。

---

## 12. 关键文件索引

- 入口：[`app.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app.py)
- 应用工厂：[`app/application.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/application.py)
- 基类：[`app/controllers/base.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/controllers/base.py)
- 认证：[`app/controllers/auth.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/controllers/auth.py)
- 页面：[`app/controllers/page.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/controllers/page.py)
- 对话控制器：[`app/controllers/chat.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/controllers/chat.py)
- 智能体服务：[`app/services/agent_service.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/services/agent_service.py)
- 数据层：[`app/models/db.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/models/db.py)、[`app/models/user.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/models/user.py)、[`app/models/message.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/models/message.py)
- 主界面模板：[`app/templates/index.html`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/templates/index.html)
- 测试：[`test/test_user.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/test/test_user.py)
- 视觉稿：[`dist/登录页面.html`](file:///e:/py/pyxm/tbyAgenticBaseWeb/dist/登录页面.html)、[`dist/后台首页.html`](file:///e:/py/pyxm/tbyAgenticBaseWeb/dist/后台首页.html)
