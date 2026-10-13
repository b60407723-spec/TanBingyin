# 变更日志

> 本文件按 **最新 → 最早** 记录本项目的关键变更。
> 格式：`## [版本或日期] YYYY-MM-DD` → 变更点列表 → 影响面 → 责任人。
> 目前项目尚未建立正式版本号，暂以日期为版本锚点，待 `agent-rules.md` 中的版本策略确定后切换为语义化版本号。

***

## \[未发布] 2026-10-14 · 启动入口端口占用处理

**整理来源**：AI 助手（修复「重新运行 `app.py` 时端口被占用报错」）。

### 变更（Changed）

- **启动健壮性** [`app.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app.py)：
  - 补充模块中文 docstring；端口提取为模块级常量 `PORT = 10086`（**取值未变**）；
  - `webapp.listen()` 包裹 `try/except OSError`：端口被占用（Windows `WinError 10048`）时输出明确中文提示并 `sys.exit(1)`，不再抛出异常堆栈。
- **新增一键重启脚本** [`restart.ps1`](file:///e:/py/pyxm/tbyAgenticBaseWeb/restart.ps1)：结束本项目运行 `app.py` 的旧实例 → 等待 10086 端口释放 → 用 `.venv` 解释器前台重启服务；文件保存为 **UTF-8 with BOM**（PowerShell 5.1 正确识别中文注释）。

### 校验（Verified）

- 旧实例占用 10086 时重复启动：输出「启动失败：端口 10086 已被占用。…」，退出码 1，无 traceback；
- 释放端口后启动：正常监听 10086，`GET /` 返回 HTTP 200；
- `powershell -ExecutionPolicy Bypass -File .\restart.ps1`：正确输出中文、停旧启新，重启后 `GET /` 返回 HTTP 200。

### 说明（Notes）

- 未改动端口取值、路由、`cookie_secret` 等运行参数；
- 端口被占用时仍需先停止旧实例；本改动仅将「难以理解的堆栈」转为「可操作的提示」。

***

## \[未发布] 2026-10-14 · 任务3（首页原型迭代）

**整理来源**：AI 助手（任务3：将 `dist/后台首页.html` 原型转换为运行时 `index.html`）。

### 变更（Changed）

- **前端页面迭代** [`app/templates/index.html`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/templates/index.html)（**仅前端，未改动任何后端业务代码**）：
  - 参照 `dist/后台首页.html` 原型，将首页由「标题 + 纯文本聊天记录 + 简陋表单」重写为 **左侧边栏 + 主对话区 + 底部 composer** 的工作台布局；
  - 代码规范对齐 `login.html`：`{% extends "base.html" %}` + `{% block body %}`、Tailwind CDN + FontAwesome CDN + 内联 `tailwind.config`、`<script id="功能名">` 分组、末尾 `window.onload` 内 `try/catch` 逐个 `addEventListener` 绑定；
  - 采用消息气泡模板 `<template id="tpl-user">` / `<template id="tpl-bot">`，欢迎 hero + 旅行主题建议卡（点击填入输入框）。
- **缺陷修复**：原 `index.html` SSE 解析处 `dataline` / `dataLine` 变量名不一致（运行期 `ReferenceError`）已随本次重写修复。

### 保留（Kept，原功能不降级）

- SSE 问答：`POST /api/chat`（`Content-Type: application/json` + `X-XSRFToken`，`ReadableStream` 逐帧解析 `delta` / `error`）；
- 历史加载：`GET /api/history?limit=50`，`{{ username }}` 展示，401 → 跳转 `/auth/login`；
- 登出：`POST /auth/logout` 带 `{% module xsrf_form_html() %}`；聊天表单同样携带 XSRF。

### 校验（Verified）

- 以 Tornado 模板引擎 `Loader.load("index.html")` + `generate(title, username, xsrf_form_html)` **渲染通过**（输出 15,266 字符，XSRF 输入框 ×2、`#chatForm` / `#chatList` / `#tpl-user` / `#tpl-bot` 均存在）；
- 后端业务代码**未改**，`agent_service.py` 编译错误等历史缺陷**依旧存在**（见下一节）。

### 说明（Notes）

- 人类手动启动项目服务，未在本次任务中启动进程；
- 后端未改动，前端功能性依赖后端接口；若 `agent_service.py` 仍未修复，则服务无法启动，本页面将无从访问。

***

## \[未发布] 2026-10-14

**整理来源**：AI 助手（任务2：学习 `services/`、`index.html`、`chat.py`、`message.py` 并维护文档）。

### 变更（Changed）

- **文档一致性校正**（依据磁盘代码实测，**未改动任何业务代码**）：
  - `architecture.md`：§1/§2/§3/§4/§5/§9 同步为「Agentica 已接入」现状（路由、目录、分层职责、启动流程、对话数据流）；新增 **§9.1 对话数据流**；新增 **§11.1 当前已知缺陷**表；重写 §11 实现状态总览、§12 关键文件索引；
  - `requirements.md`：§2.3 R-AGENT 由「预留」改为「已实现」；§4 接口清单补 `/api/chat`、`/api/history`、`/api/health` 并更正「待挂载」描述；§6 `.env` 加载方式更正为「Service 层 `load_dotenv()`」；§8 Backlog 重排；
  - `agent-rules.md`：§7 遗留项按实测优先级重排。

### 已知（Known）—— 本次学习新发现（**均未修改**）

- **阻塞级**：`app/services/agent_service.py` **当前无法编译**——第 47/48 行行尾为中文全角逗号 `，`(U+FF0C)，触发 `SyntaxError: invalid character`；另有 L61-63 缺英文逗号、`_agents = Dict[str,Agent]={}` 写法错误、`TOOL_NAMES` 拼写 `builtin_task_toll`、`done` 事件 `yield` 缩进过深；
- `app/controllers/chat.py`：`done` 分支用 `event.get("answer","")` 与 Service 产出的 `text` 键不一致（assistant 消息永不落库）；`self.lsse(...)` 拼写错误（应为 `self.sse`）；
- `app/templates/index.html`：SSE 解析处声明 `dataline` 却判断 `dataLine`，运行期 `ReferenceError`；
- `app/models/message.py`：`count()` 的无参分支缺 `return`；
- `app/controllers/page.py`：`HealthHandler.get()` 构造 `health_info` 后未 `self.write(...)`。

### 说明（Notes）

- 本次仅为**学习归档 + 文档维护**，未新增/修改任何业务代码；
- 上述「阻塞级」问题意味着当前磁盘版本的服务**无法直接启动**；仍在提供服务的进程对应修改前的内存代码。

***

## \[未发布] 2026-10-13

**整理来源**：AI 助手（环境修复 + 文档一致性校正）。

### 变更（Changed）

- **环境（venv 迁移）**：`.venv` 系由旧路径复制而来，`Scripts\*.exe`（pip.exe 等）内嵌旧绝对路径而失效；已在当前路径 `E:\py\pyxm\tbyAgenticBaseWeb\.venv` 重建并重装依赖，`pip.exe` / `agentica.exe` 恢复可用；
- **新增** **`requirements.txt`**：锁定 46 个依赖（`pip freeze` 导出），环境可复现；
- **文档一致性校正**：
  - 修正 `docx/*.md` 中指向旧路径 `E:\class_1009\...` 的 `file://` 链接为当前路径；
  - `requirements.md` / `agent-rules.md`：更正「`db.py` 的 `init_db()` 缩进错误」——实测**已正确**，原描述作废；
  - `app/models/__init__.py`：docstring 由「SQLAlchemy ORM」更正为「SQLite 直连 + Repository」，与实际实现一致。

### 说明（Notes）

- 本次仅涉及环境与文档，**未改动业务逻辑**；
- 上一版（2026-10-11）「已知（Known）」中关于 `db.py` 缩进的条目**作废**，以本条目为准；
- `cookie_secret` 硬编码、`.env` 未加载、`==` 比对、路由未挂载等缺口**仍然存在**，未在本条目处理。

***

## \[未发布] 2026-10-11

**整理来源**：AI 助手对本仓库当前状态的学习与归档。

### 新增（New）

- 归档项目架构基线：[`docx/architecture.md`](file:///e:/py/pyxm/tbyAgenticBaseWeb/docx/architecture.md)；
- 归档需求与验收：[`docx/requirements.md`](file:///e:/py/pyxm/tbyAgenticBaseWeb/docx/requirements.md)；
- 建立协作规则初稿：[`docx/agent-rules.md`](file:///e:/py/pyxm/tbyAgenticBaseWeb/docx/agent-rules.md)。

### 已知（Known）—— 现存代码中的问题

- `app/models/db.py`：`init_db()` 内 `with` 块之后的 `conn.execute(...)` 与 `with` 同级缩进，会导致 `IndentationError`；
- `app/application.py`：`RegisterHandler`、`HealthHandler` 已实现但未加入路由表；
- `app/models/__init__.py`：docstring 声明使用 SQLAlchemy ORM，与实际 SQLite 直连不一致；
- `app/controllers/auth.py`：`get_argument("next", "/")` 在 POST 表单下无法从 body 获取，建议改为 `get_query_argument`；
- `app/models/user.py`：哈希结果直接 `==` 比对，建议改用 `hmac.compare_digest`；
- `app.py`：未加载 `.env`，`.env` 中的 `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `MODEL_ID` 实际未被读取；
- `app.py`：`cookie_secret` 硬编码为 `"agentica-demo-secret"`；
- 空文件（占位）：`app/models/message.py`、`app/controllers/chat.py`、`app/services/__init__.py`、`app/templates/register.html`、`app/static/css/style.css`、`app/static/js/app.js`。

### 说明（Notes）

- 现有代码由人类开发者完成，本次 AI 只做学习归档，未修改任何业务代码；
- 后续 AI 在接手任务时，需先修复上述 Known 项，再扩展新能力。

***

## \[基线] 2026-10-9

**整理来源**：从代码与目录结构推断的人类开发历史基线，非精确。

### 已完成

- 建立项目根与 `app/` MVC 分层骨架；
- 引入 Tornado，实现 `make_app()` 与 `app.py` 入口；
- 引入 SQLite，定义 `users` / `messages` 表；
- 实现 `UserRepository`（PBKDF2 哈希 + salt + UNIQUE 用户名）；
- 实现 `BaseHandler`（`get_current_user` / `write_json` / `sse`）；
- 实现 `LoginHandler` / `RegisterHandler` / `LogoutHandler` / `IndexHandler` / `HealthHandler`；
- 编写登录页与首页模板，母版 `base.html`；
- 编写 `test/test_user.py` 脚本级测试；
- 交付登录页视觉稿 `dist/登录页面.html`（Tailwind + FontAwesome）。

### 未启动

- Agentica 智能体集成；
- 聊天 / 会话 / 消息持久化业务；
- 前端运行时样式与交互脚本；
- 单元测试 / 集成测试框架（pytest）；
- 部署脚本、容器化、CI。

