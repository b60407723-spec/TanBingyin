# 需求说明

> 本文件汇总当前已明确的产品需求、验收标准，以及后续迭代的候选项。
> 编号规则：`R-<模块>-<序号>`，如 `R-AUTH-01`。

---

## 1. 技术栈（已选型）

| 类别 | 选型 | 说明 |
| --- | --- | --- |
| 语言 | Python 3.12 | 依赖 `pyvenv.cfg` 中的解释器 |
| Web 框架 | Tornado | 异步 IO，`RequestHandler` + 模板 + 静态文件 |
| 智能体框架 | Agentica（venv 内已安装） | 面向多智能体编排、工具、记忆、Checkpoint |
| LLM 协议 | OpenAI 兼容端点 | `.env` 中 `OPENAI_BASE_URL` 指定网关 |
| 存储 | SQLite（`sqlite3`） | 无 ORM，Repository 直接 SQL |
| 密码哈希 | PBKDF2-HMAC-SHA256 | 独立 salt，`100_000` 次迭代 |
| 模板 | Tornado 内置模板 | `{% extends %}` / `{% block %}` / `{% module %}` |
| 前端 | 原生 HTML + CSS + JS | 视觉稿使用 Tailwind CDN，落地后转本地文件 |
| 测试 | 脚本式 `python test/test_user.py` | 未使用 pytest，允许后续引入 |
| 运行端口 | `10086` | 见 `app.py` |

---

## 2. 功能需求

### 2.1 用户认证（R-AUTH）

- **R-AUTH-01** 支持用户名 + 密码注册，用户名唯一（`UNIQUE` 约束）；两次密码输入需一致。
- **R-AUTH-02** 支持登录，用户名 / 密码正确则写入签名 Cookie `username`。
- **R-AUTH-03** 支持登出，清除 `username` Cookie 并跳回登录页。
- **R-AUTH-04** 需要登录的页面必须使用 `@tornado.web.authenticated` 保护。
- **R-AUTH-05** 密码存储必须为 PBKDF2 哈希 + 独立 salt，禁止明文。
- **R-AUTH-06** 所有 `POST` 表单必须携带 XSRF token。
- **R-AUTH-07** 登录成功后按 `next` 查询参数跳转，缺省回 `/`。

验收：
- 注册新用户 → 落库 `users`，`salt` 与 `password_hash` 均非空；
- 错误密码登录 → 返回 401，页面回显「用户名或密码错误」；
- 正确密码登录 → 写 Cookie，跳转目标页；
- 无 Cookie 访问 `/` → 重定向到 `/auth/login`。

### 2.2 主工作台（R-HOME）

- **R-HOME-01** 首页展示「多智能体规划工作台」标题与当前用户名。
- **R-HOME-02** 首页提供退出登录表单。
- **R-HOME-03** 承载对话窗口（消息气泡、SSE 流式增量渲染）、新建对话与历史回显。
- **R-HOME-04** 页面布局 / 样式以 `dist/后台首页.html` 原型为准（左侧边栏 + 主对话区 + 底部 composer），代码规范对齐 `login.html`；实现须**保留原有全部功能**（SSE 问答、历史加载、登出、XSRF），仅做原型转换。

### 2.3 智能体对话（R-AGENT，已实现）

- **R-AGENT-01** 前端向 `/api/chat` 提交用户输入，后端经 `agent_service.stream_answer()` 组装并调用 Agentica 智能体后返回；
- **R-AGENT-02** 长任务输出走 SSE，事件经 `BaseHandler.sse()` 打包（事件名 `delta` / `tool` / `reasoning` / `done`）；
- **R-AGENT-03** 每条消息落 `messages` 表（含 `username`、`role`、`content`），由 `MessageRepository.save` 负责；
- **R-AGENT-04** 历史会话按 `username` 分页查询，接口 `/api/history?limit=50`；
- **R-AGENT-05** 智能体配置（`MODEL_ID`、`OPENAI_BASE_URL`、`OPENAI_API_KEY`）通过 `.env` 注入，由 Service 层 `load_dotenv()` 加载，禁止硬编码。

> 现状：功能链路已打通，但存在若干缺陷（详见 [`architecture.md`](file:///e:/py/pyxm/tbyAgenticBaseWeb/docx/architecture.md) §11.1），其中 `agent_service.py` 当前**无法编译**。

### 2.4 健康检查（R-HEALTH）

- **R-HEALTH-01** 提供 `/health` 端点，返回模型 / API Key 配置状态；
- **R-HEALTH-02** 该端点在生产环境必须受鉴权保护或删除。

---

## 3. 非功能需求

- **NFR-01 安全**：启用 XSRF；Cookie 使用签名；密码不明文；敏感密钥走环境变量。
- **NFR-02 分层**：Controller 不写 SQL；Service 独占 Agentica；Model 不依赖 Tornado。
- **NFR-03 可读性**：所有 Python 模块顶部保留中文 docstring，说明模块职责。
- **NFR-04 编码**：JSON 输出 `ensure_ascii=False`，字符集固定 UTF-8。
- **NFR-05 幂等**：`init_db()` 使用 `CREATE TABLE IF NOT EXISTS`，可重复调用。
- **NFR-06 端口**：默认 `10086`，生产可通过环境变量覆盖。
- **NFR-07 前端**：静态资源本地化，禁止在运行时依赖公共 CDN。

> 偏差记录：当前 `login.html` / `index.html` 仍通过 CDN 引入 Tailwind 与 FontAwesome，尚未落地为本地静态资源，见 `architecture.md` §10 与本文 §8 Backlog。

---

## 4. 接口清单（HTTP）

| 方法 | 路径 | 说明 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| GET | `/` | 主工作台（侧边栏 + 对话区，原型见 `dist/后台首页.html`） | — | HTML |
| GET | `/auth/login` | 登录页 | — | HTML |
| POST | `/auth/login` | 登录 | `username`, `password`, `next?` | 302 或错误页 |
| GET | `/auth/register` | 注册页（模板占位） | — | HTML |
| POST | `/auth/register` | 注册 | `username`, `password`, `password2` | 302 或错误页 |
| POST | `/auth/logout` | 登出 | — | 302 |
| GET | `/api/health` | 健康检查（实现未完成） | — | JSON |
| POST | `/api/chat` | 智能体问答（SSE） | JSON `{message}` | `text/event-stream` |
| GET | `/api/history` | 当前用户历史消息 | `limit?`（默认 50） | JSON |
| GET | `/static/(.*)` | 静态资源 | — | 二进制 / 文本 |

> `/api/*` 未登录时统一返回 `401 JSON` + `login_url`（前端 `fetch` 捕获后跳转）。

---

## 5. 数据字典

`users`
| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| username | TEXT | NOT NULL, UNIQUE | 用户名 |
| password_hash | TEXT | NOT NULL | PBKDF2 十六进制哈希 |
| salt | TEXT | NOT NULL | 16 字节随机盐的 hex |
| created_at | TEXT | DEFAULT now(localtime) | 创建时间 |

`messages`
| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| username | TEXT | NOT NULL, 默认 `''` | 归属用户 |
| role | TEXT | NOT NULL | `user` / `assistant` / `system` / `tool` |
| content | TEXT | NOT NULL | 消息内容 |
| created_at | TEXT | DEFAULT now(localtime) | 创建时间 |

---

## 6. 环境与配置

`.env`
```
OPENAI_BASE_URL=http://127.0.0.1:11435/v1
OPENAI_API_KEY=***
MODEL_ID=***
```

加载方式（当前状态）：
- `.env` 由 **Service 层** [`app/services/agent_service.py`](file:///e:/py/pyxm/tbyAgenticBaseWeb/app/services/agent_service.py) 顶部的 `load_dotenv()` 加载；
- `app.py` / `make_app()` 本身**未**加载 `.env`；
- `HealthHandler` 使用 `os.environ.get(...)` 读取，依赖上游（Service 层加载或外部注入）。

后续改进（建议）：
- 在 `make_app()` 启动时统一加载 `.env`，避免 `HealthHandler` 早于首次 Service 调用时读不到配置。

---

## 7. 测试需求

- **T-01** `test/test_user.py` 直接可运行：`python test/test_user.py`；
- **T-02** 断言项：正确密码可登录、错误密码登录失败、错误用户名登录失败；
- **T-03** 测试前必须清理 `users` 表内同用户名记录，测试后同样清理；
- **T-04** 测试用例以 `assert` 直接断言，失败抛出，成功打印「所有测试用例通过！」；
- **T-05** 后续如引入 pytest，需保持向后兼容：脚本式执行仍应可用。

---

## 8. 已知缺口（Backlog）

- [x] `RegisterHandler` / `HealthHandler` 已在 `make_app()` 中挂载，可直接访问；
- [x] `app/models/message.py`、`app/controllers/chat.py`、`app/services/agent_service.py` 已实现；
- [ ] `app/services/agent_service.py` **当前无法编译**（第 47/48 行中文全角逗号），需修复后服务才可加载；
- [ ] `app/controllers/chat.py`：`done` 分支键名 `answer` 与 Service 产出的 `text` 不一致（assistant 不落库）、`self.lsse(...)` 拼写错误；
- [ ] `app/controllers/page.py`：`HealthHandler.get()` 未输出响应体；
- [ ] `app/models/message.py`：`count()` 的无参分支缺 `return`；
- [x] `app/templates/index.html`：SSE 解析处变量名 `dataline` / `dataLine` 不一致 —— **已随任务3 首页原型迭代修复**；
- [x] `app/templates/index.html`：页面已按 `dist/后台首页.html` 原型重写（侧边栏 + 对话区），并保留原有功能（见 R-HOME-04）；
- [ ] `app/templates/register.html`、`app/static/css/style.css`、`app/static/js/app.js`、`app/static/js/login.js` 为空文件；
- [x] ~~`db.py` 中 `init_db()` 缩进错误~~ **已核实修复**：实测 `init_db()` 缩进正确、可正常幂等建表，原描述有误；
- [x] `models/__init__.py` 描述**已更正**为「SQLite 直连 + Repository」，与实际实现一致；
- [ ] `.env` 仅在 Service 层加载，`app.py` 未加载；
- [ ] `cookie_secret` 硬编码，生产不安全；
- [ ] PBKDF2 结果直接 `==` 比对，建议改用 `hmac.compare_digest`；
- [ ] `LoginHandler` 的 `self.get_argument("next", "/")` 在 POST 表单中无法从 body 获取，建议改为 `self.get_query_argument`；
- [ ] 视觉稿（Tailwind CDN、外部插画 API）尚未转成运行时静态资源。

---

## 9. 验收口径

一项功能被认为「完成」需要同时满足：
1. 对应路由已挂载并可通过浏览器触达；
2. Controller / Repository / 模板三层实现完备，无空文件；
3. 通过对应的测试（脚本或 pytest）；
4. 相关文档（本文件、`architecture.md`、`changelog.md`）已同步更新；
5. 无违反第 3 节 NFR 的实现细节。
