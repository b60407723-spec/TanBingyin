# 项目协作规则

> 本文件约定本项目人类开发者与 AI 助手协作时的规则与流程。
> 后续所有 AI 参与的任务必须遵守本文件；如与本文件冲突，以本文件为准。

---

## 1、发布决策权

- **1.1** 发布决策权归属于**项目 Owner（人类开发者）**，AI 不擅自发布、不擅自合并、不擅自推送远端；
- **1.2** AI 在本地完成变更并自测通过后，须在 `changelog.md` 追加变更条目并等待人类 review；
- **1.3** AI 不得执行以下操作（除非人类明确书面要求）：
  - `git push`、`git push --force`、`git merge`、`git rebase`；
  - 修改 `requirements.txt` / `pyproject.toml` / `Dockerfile` / CI 配置；
  - 修改 `.env` 中的密钥；
  - 修改端口、cookie_secret、数据库文件路径等运行参数；
- **1.4** AI 若发现影响线上运行的高危问题，应在回复中明确标注「**阻塞级**」并暂停后续动作等待决策；
- **1.5** 每一次 AI 提交前，必须：
  1. 说明本次改动的范围与风险；
  2. 说明已运行哪些测试以及结果；
  3. 更新 `changelog.md`；
  4. 由人类 review 后才允许进入 git 提交流程。

---

## 2、版本号规则

- **2.1** 采用语义化版本（SemVer）：`MAJOR.MINOR.PATCH`；
  - `MAJOR`：架构级 / 不兼容变更（例如切换 Web 框架、更换存储引擎）；
  - `MINOR`：向后兼容的新增能力（新增智能体、新增路由、新增页面）；
  - `PATCH`：向后兼容的缺陷修复（bug fix、文档修正）；
- **2.2** 版本号统一在 [`docx/changelog.md`](file:///e:/py/pyxm/tbyAgenticBaseWeb/docx/changelog.md) 顶部登记；
- **2.3** 版本号与 git tag 一一对应：`v0.1.0`、`v0.1.1` ……；
- **2.4** 未 tag 之前使用日期作为临时版本锚点，形如 `[未发布] 2026-10-11`；
- **2.5** 版本号只在人类确认后递增；AI 不擅自 bump。

---

## 3、工作流范式

### 3.1 通用流程

```
需求 → 设计 → 编码 → 自测 → 文档 → 提交 → Review → 合并 → 发布
```

- **需求**：写清「做什么 / 不做什么 / 验收标准」，落在 `requirements.md` 或任务卡；
- **设计**：确认落在哪一层（controller / service / model / template）；
- **编码**：遵守第 4 节的编码规范；
- **自测**：至少覆盖变更模块的现有测试 + 新增断言；
- **文档**：同步 `architecture.md` / `requirements.md` / `changelog.md`；
- **提交**：单次提交聚焦一件事，禁止夹带格式化；
- **Review**：由人类执行；
- **合并 / 发布**：由人类执行。

### 3.2 AI 参与任务的强制流程

1. **对齐**：AI 在动手前，用 3–5 行描述本次要做的事、涉及哪些文件；
2. **只读优先**：先 `Read` / `Grep` / `SearchCodebase`，再 `Write` / `SearchReplace`；
3. **最小改动**：不夹带无关格式化、不重命名无关变量；
4. **不越权**：不修改第 1 节列出的敏感项；
5. **自检**：修改完成后跑一遍相关测试；
6. **归档**：更新 `changelog.md` 与相关文档；
7. **交付**：向人类汇报变更清单、测试结论、风险与遗留项。

### 3.3 代码审查要点

AI 提交 Review 时，人类审查应重点看：
- 是否遵守 MVC 分层（第 4 节）；
- Controller 是否引入了 SQL / Agentica 逻辑；
- Service 是否成为唯一的 Agentica 入口；
- 是否有新增的密钥硬编码；
- 是否破坏现有测试；
- 是否有未同步的文档。

### 3.4 测试要求

- 现有基线：`python test/test_user.py` 必须绿；
- 每次变更涉及 `UserRepository` / 认证 → 必须扩展 `test_user.py`；
- 新增 Service → 必须补充至少 1 个冒烟测试（脚本或 pytest）；
- 涉及并发 / SSE → 建议使用 Tornado 的 `AsyncHTTPTestCase`。

---

## 4、编码规范

### 4.1 Python

- 语言：Python 3.12；
- 每个模块顶部保留中文 docstring，说明职责；
- 命名：
  - 模块 / 文件：`snake_case`；
  - 类：`PascalCase`；
  - 函数 / 变量：`snake_case`；
  - 常量：`UPPER_SNAKE_CASE`；
- 不使用裸 `except:`；捕获 `sqlite3.IntegrityError` 等具体异常；
- 类型注解：新代码尽量补齐，旧代码不强推。

### 4.2 分层约束

| 层 | 允许引用 | 禁止引用 |
| --- | --- | --- |
| `controllers/` | `tornado`、`app.models.*`、`app.services.*` | 直接 `sqlite3`、`agentica` |
| `services/` | `agentica`、`app.models.*` | `tornado` |
| `models/` | `sqlite3`、标准库、`agentica.db.*` | `tornado`、`app.controllers.*` |
| `templates/` | Tornado 模板语法 | 内联业务逻辑 |

### 4.3 Tornado 路由与 Handler

- 每条路由写在 `app/application.py` 的 `make_app()` 内，保持单一入口；
- Handler 类放在 `controllers/` 下，一个业务一个模块；
- 通用能力抽到 `BaseHandler`：`get_current_user` / `write_json` / `sse`；
- 需要登录的 Handler 使用 `@tornado.web.authenticated`。

### 4.4 数据库与密码

- 表结构只在 `app/models/db.py` 的 `init_db()` 中定义；
- 每张表配套一个 `*Repository`，静态方法聚合 SQL；
- 密码只存 `hash + salt`，salt 长度 16 字节，算法 PBKDF2-HMAC-SHA256；
- 密码校验最终使用 `hmac.compare_digest`（现有实现使用 `==`，需修正）；
- 数据库文件路径集中在 `DB_PATH`，业务代码不得硬编码。

### 4.5 模板与静态资源

- 模板继承 `base.html`，通过 `{% block body %}` / `{% block scripts %}` 覆盖；
- 所有 `POST` 表单必须包含 `{% module xsrf_form_html() %}`；
- 静态资源本地化到 `app/static/{css,js}`，禁止在运行时依赖公共 CDN；
- 高保真视觉稿放在 `dist/`，仅作为参考。

### 4.6 JSON / SSE

- JSON 响应统一走 `BaseHandler.write_json(data, status)`，`ensure_ascii=False`、字符集 UTF-8；
- SSE 事件统一走 `BaseHandler.sse(event, data)`；
- 事件命名：`snake_case`，如 `message_delta`、`tool_call`、`run_done`。

---

## 5、禁止项

- **5.1** 禁止修改本目录外的任何文件；
- **5.2** 禁止删除 `.env`、`database/app.db`、`test/`、`dist/` 目录；
- **5.3** 禁止在业务代码中硬编码 `cookie_secret`、API Key、数据库路径；
- **5.4** 禁止在 Controller 中直接写 SQL；
- **5.5** 禁止把 Agentica 相关 import 泄漏到 Controller 或 Template；
- **5.6** 禁止使用交互式命令（`git rebase -i`、`git add -i`、`vim`、`less` 等）；
- **5.7** 禁止向 `.venv/` 目录提交任何变更；
- **5.8** 禁止在 `dist/` 目录内生成运行时代码；`dist/` 仅作为视觉稿归档。

---

## 6、沟通约定

- 语言：中文；代码注释与文档同样使用中文；
- 汇报结构：结论 → 证据 → 风险 → 下一步；
- 引用代码时使用 `[文件名](file:///绝对路径)` 链接形式，不使用行号平铺；
- 遇到不确定项时，先 `AskUserQuestion`，避免猜测性编码。

---

## 7、遗留项（本次学习发现，建议后续处理）

按优先级排序：
1. **P0（阻塞）**：`app/services/agent_service.py` 当前**无法编译**（第 47/48 行中文全角逗号 `，`），服务加载即失败，须优先修复；
2. **P1（可用性）**：`app/controllers/chat.py` 的 `done` 分支键名不一致（`answer` ↔ `text`）、`self.lsse` 拼写错误；`HealthHandler.get()` 未输出响应体；`message.py::count()` 无参分支缺 `return`；（`index.html` SSE 解析变量名不一致已于任务3 修复）；
3. **P1（安全）**：`cookie_secret` 外置；PBKDF2 比对改用 `hmac.compare_digest`；
4. **P1（已完成）**：`RegisterHandler`、`HealthHandler` 已挂载到路由表；`/api/chat`、`/api/history` 已挂载；
5. **P2（一致性）**：`models/__init__.py` 描述与实际实现（SQLite 直连）已更正；
6. **P2（体验）**：`LoginHandler` 的 `next` 参数取用方式修正为 `get_query_argument`；
7. **P2（配置）**：`.env` 目前仅在 Service 层 `load_dotenv()`；建议在 `make_app()` 统一加载；
8. **P3（业务/前端）**：补全 `register.html`、`style.css`、`app.js`、`login.js`；对 Service 层补充冒烟测试。

上述条目在未完成前，本文件不视为「规则闭环」。
