# TB YAgenticBaseWeb · 多智能体规划工作台

基于 **Tornado + Agentica + SQLite** 的智能体 Web 工作台。项目提供完整的用户体系（注册 / 登录 / 登出），并接入 Agentica 智能体编排，打通「提问 → 智能体流式回答（SSE）→ 消息落库 → 历史回显」的最小闭环。

内置一个名为「旅行规划师」的智能体：可拆解任务、并行派出子智能体调研、查询天气、并在长期记忆中保存用户的出行偏好。

## 功能特性

- **用户体系**：用户名 + 密码注册、登录、登出，密码使用 PBKDF2-HMAC-SHA256 加盐哈希存储。
- **智能体对话**：`POST /api/chat` 以 SSE 流式返回，逐帧增量渲染回答、工具调用与推理过程。
- **对话历史**：按登录用户隔离，`GET /api/history` 分页读取最近消息，页面加载时自动回显。
- **多智能体能力**：任务拆解（Todo）、子智能体并行调研（Task）、天气查询、长期记忆、联网搜索。
- **工作台界面**：左侧边栏 + 主对话区 + 底部输入框的现代工作台布局（Tailwind + FontAwesome）。

## 技术栈

| 类别 | 选型 |
| --- | --- |
| 语言 | Python 3.12 |
| Web 框架 | Tornado（异步 IO + 内置模板引擎） |
| 智能体框架 | Agentica |
| LLM 协议 | OpenAI 兼容端点（`.env` 配置网关） |
| 存储 | SQLite（`sqlite3` 标准库 + Repository 模式） |
| 密码哈希 | PBKDF2-HMAC-SHA256（独立随机 salt，100,000 次迭代） |
| 前端 | 原生 HTML + CSS + JS（Tailwind / FontAwesome） |

## 目录结构

```
tbyAgenticBaseWeb/
├── app.py                      # 服务入口，监听 10086 端口
├── app/
│   ├── application.py          # Tornado Application 工厂 make_app()
│   ├── controllers/            # 控制层：RequestHandler
│   │   ├── base.py             #   BaseHandler：get_current_user / write_json / sse
│   │   ├── auth.py             #   登录 / 注册 / 登出
│   │   ├── page.py             #   首页 / 健康检查
│   │   └── chat.py             #   对话（SSE）/ 历史查询
│   ├── models/                 # 数据层：Repository 模式
│   │   ├── db.py               #   SQLite 连接工厂 + init_db() 建表
│   │   ├── user.py             #   UserRepository：注册 / 校验 / 查询
│   │   └── message.py          #   MessageRepository：对话落库 / 近 N 条查询
│   ├── services/
│   │   └── agent_service.py    # 服务层：Agentica 智能体组装 / 缓存 / 流式回答
│   ├── static/                 # CSS / JS 静态资源
│   └── templates/              # Tornado 模板：base / login / register / index
├── test/
│   └── test_user.py            # 用户注册 / 校验的脚本级测试
├── docx/                       # 项目文档（需求、架构、变更日志、协作规则）
├── dist/                       # 高保真前端视觉原型
├── requirements.txt            # 依赖清单
├── .env.example                # 环境变量模板
└── restart.ps1                 # Windows 一键重启脚本
```

## 快速开始

### 1. 环境要求

- Python 3.12（建议使用虚拟环境）
- Windows / macOS / Linux

### 2. 获取代码并安装依赖

```bash
git clone https://github.com/b60407723-spec/TanBingyin.git
cd TanBingyin

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置模型端点

复制 `.env.example` 为 `.env`，填入你自己的 OpenAI 兼容端点信息：

```dotenv
OPENAI_BASE_URL=https://your-endpoint.example.com/v1
OPENAI_API_KEY=your_api_key_here
MODEL_ID=your_model_id
```

> `.env` 已加入 `.gitignore`，不会被提交到仓库。三项缺一不可，否则服务启动后调用对话接口会提示缺少环境变量。

### 4. 启动服务

```bash
python app.py
```

启动成功后访问：<http://localhost:10086/>

首次访问需先注册账号，然后登录进入工作台。

### Windows 一键重启（可选）

修改代码后可用脚本快速重启（自动结束旧实例、等待端口释放、用 `.venv` 重新启动）：

```powershell
powershell -ExecutionPolicy Bypass -File .\restart.ps1
```

## 接口一览

| 方法 | 路径 | 说明 | 是否需登录 |
| --- | --- | --- | --- |
| GET | `/` | 主工作台页面 | 是 |
| GET | `/auth/login` | 登录页 | 否 |
| POST | `/auth/login` | 登录（写入签名 Cookie） | 否 |
| GET | `/auth/register` | 注册页 | 否 |
| POST | `/auth/register` | 注册（创建用户） | 否 |
| POST | `/auth/logout` | 登出（清除 Cookie） | 否 |
| GET | `/api/health` | 健康检查（模型 / Key 配置状态） | 否 |
| POST | `/api/chat` | 智能体问答（SSE 流式） | 是 |
| GET | `/api/history` | 当前用户历史消息（`limit`，默认 50） | 是 |
| GET | `/static/(.*)` | 静态资源 | 否 |

> 页面接口未登录时 302 跳转到 `/auth/login`；`/api/*` 数据接口未登录时统一返回 `401 JSON` + `login_url`，由前端 `fetch` 捕获后跳转。

### SSE 事件格式

`POST /api/chat` 返回 `text/event-stream`，事件类型包括：

| 事件 | 说明 |
| --- | --- |
| `delta` | 正文增量文本 |
| `tool` | 工具调用（工具名 + 参数） |
| `reasoning` | 推理过程增量 |
| `done` | 回答结束（此时 assistant 消息落库） |
| `error` | 异常信息 |

## 数据模型

`users`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| username | TEXT | 用户名，唯一 |
| password_hash | TEXT | PBKDF2 十六进制哈希 |
| salt | TEXT | 16 字节随机盐（hex） |
| created_at | TEXT | 创建时间 |

`messages`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| username | TEXT | 归属用户 |
| role | TEXT | `user` / `assistant` / `system` / `tool` |
| content | TEXT | 消息内容 |
| created_at | TEXT | 创建时间 |

> 数据库文件位于 `database/app.db`，服务启动时自动建库建表，无需手动初始化。

## 运行测试

```bash
python test/test_user.py
```

覆盖用户注册与登录校验（正确密码登录成功、错误密码失败、错误用户名失败），全部通过后输出「所有测试用例通过！」。

## 分层架构

项目采用 MVC 分层，约束如下：

- **Controller**（`app/controllers/`）：处理 HTTP，不直接写 SQL。
- **Model**（`app/models/`）：表结构、连接工厂、SQL 封装；不依赖 Tornado。
- **Service**（`app/services/`）：唯一允许引用 `agentica` 的层；负责智能体组装、按用户缓存与流式调度。
- **View**（`app/templates/`）：Tornado 内置模板，继承 `base.html`。

详细设计见 [`docx/architecture.md`](docx/architecture.md)，需求与验收标准见 [`docx/requirements.md`](docx/requirements.md)。

## 注意事项

- 当前 `debug=True` 且 `cookie_secret` 为示例值，**仅适用于本地开发**；生产环境请改为 `debug=False` 并替换为随机密钥（建议外置到环境变量）。
- `login.html` / `index.html` 通过 CDN 引入 Tailwind 与 FontAwesome，如需离线部署请将静态资源本地化。
- 请勿将 `.env`、`database/*.db`、`workspace/` 等运行时数据提交到仓库（已在 `.gitignore` 中忽略）。

## 许可证

本项目基于 [BSD 3-Clause License](LICENSE) 开源。
