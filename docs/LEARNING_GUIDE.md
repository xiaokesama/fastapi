# StudyTrack 手敲学习路线

这份路线建议用 **8～12 天**完成。目标不是“把代码复制运行”，而是每完成一个阶段，都能解释它为什么这样写，并能独立复现。

## 一、手敲规则

1. 先读当前阶段说明，再关掉参考代码自己写。
2. 每个文件写完后运行一次项目，不要积累几十个错误再调试。
3. 遇到报错时记录三件事：报错原文、原因、修复方法。
4. 每完成一个阶段做一次 Git 提交，提交信息写清楚学到了什么。
5. 能运行后，尝试删掉一行、改错一个类型、少写一个依赖，观察 FastAPI 如何报错。
6. 最后不看原代码，自己再写一遍核心登录流程和任务 CRUD。

推荐建立自己的学习记录文件，例如：

```text
notes/
├── 01-pydantic.md
├── 02-sqlalchemy.md
├── 03-jwt.md
├── 04-errors.md
└── 05-questions.md
```

## 二、阶段路线

### 阶段 1：启动最小应用

**目标**

- 理解 FastAPI 实例、路由、自动文档和 Uvicorn。
- 知道 `app/main.py` 为什么是应用入口。

**手敲文件**

- `pyproject.toml`
- `app/__init__.py`
- `app/main.py`
- `app/api/router.py`

**最小验收**

```powershell
uv run uvicorn app.main:app --reload
```

访问 `/docs` 能看到接口文档，`/health` 返回 `{"status":"ok"}`。

**动手实验**

- 增加一个 `GET /hello/{name}`，返回一句问候。
- 把 `name` 改成 `int`，访问时传字符串，阅读 422 响应。
- 在函数参数中给 `name` 加 `Query` 约束。

---

### 阶段 2：配置与数据库连接

**目标**

- 理解 `BaseSettings`、环境变量和 `.env`。
- 理解异步 SQLAlchemy 的 Engine、Session 和依赖注入。

**手敲文件**

- `app/core/config.py`
- `app/db/base.py`
- `app/db/session.py`
- `app/db/init_db.py`

**重点问题**

- 为什么每个请求创建一个 Session？
- 为什么使用 `expire_on_commit=False`？
- SQLite 为什么需要启用 `PRAGMA foreign_keys=ON`？
- `yield` 依赖在请求结束后发生了什么？

**动手实验**

- 把 `SQL_ECHO=true`，观察实际操作数据库时的 SQL。
- 故意写错数据库路径，阅读启动错误。
- 在 `get_db` 中去掉异常回滚，思考事务风险。

---

### 阶段 3：SQLAlchemy 数据模型

**目标**

- 掌握一对多关系和双向 `relationship`。
- 理解外键、唯一索引、级联删除和枚举字段。

**手敲文件**

- `app/models/enums.py`
- `app/models/mixins.py`
- `app/models/user.py`
- `app/models/course.py`
- `app/models/task.py`
- `app/models/study_log.py`
- `app/models/__init__.py`

**验收**

启动应用后生成 `study_tracker.db`，包含四张表：

```text
users
courses
tasks
study_logs
```

使用 DB Browser for SQLite 或 PyCharm 数据库工具查看表结构、外键和索引。

**重点问题**

- `owner_id`、`course_id`、`task_id` 分别解决什么问题？
- 为什么 `StudyLog.task_id` 可以为空？
- `ondelete="CASCADE"` 和 `ondelete="SET NULL"` 的区别是什么？
- SQLAlchemy 的 `Enum` 在 SQLite 中怎样保存？

**动手实验**

- 给 `Course` 增加一个 `sort_order` 字段。
- 思考修改模型后，为什么已有 SQLite 表不会自动增加列。

---

### 阶段 4：Pydantic 请求与响应模型

**目标**

- 区分“数据库模型”和“接口模型”。
- 掌握字段校验、默认值、`from_attributes` 和 `exclude_unset`。

**手敲文件**

- `app/schemas/user.py`
- `app/schemas/auth.py`
- `app/schemas/course.py`
- `app/schemas/task.py`
- `app/schemas/study_log.py`
- `app/schemas/stats.py`

**验收**

- 提交空标题应得到 422。
- 非法邮箱应得到 422。
- 优先级只允许 `low / medium / high`。
- 响应中绝不出现 `hashed_password`。

**重点问题**

- `TaskCreate` 和 `TaskUpdate` 为什么不能共用一个模型？
- `model_dump(exclude_unset=True)` 解决什么问题？
- 可选字段的“没传”和“传 null”有什么区别？

**动手实验**

- 给项目名称增加唯一性校验。
- 给截止日期增加“不能早于今天”的校验，并考虑更新接口为什么会更复杂。

---

### 阶段 5：密码与 JWT

**目标**

- 理解密码只能存哈希，不能存明文。
- 理解 JWT 的签名、过期时间和 Bearer Token。

**手敲文件**

- `app/core/security.py`
- `app/core/exceptions.py`
- `app/services/auth_service.py`
- `app/api/deps.py`
- `app/api/routes/auth.py`

**验收**

注册 → 登录 → 用 Token 请求 `/auth/me`。

**重点问题**

- 为什么登录时比较的是哈希，而不是解密密码？
- JWT 的 `sub` 为什么推荐放字符串？
- Token 被篡改后会在哪一步失败？
- `OAuth2PasswordBearer` 和 Swagger 的 Authorize 按钮怎样配合？

**动手实验**

- 把 Token 有效期改成 1 分钟，观察过期响应。
- 用同一用户名大小写不同进行注册，验证冲突逻辑。
- 在 JWT payload 中加入角色，但暂不实现权限。

---

### 阶段 6：学习项目与任务 CRUD

**目标**

- 掌握 Router、Service、Schema 的职责拆分。
- 学会“当前用户数据隔离”和分页筛选。

**手敲文件**

- `app/services/course_service.py`
- `app/services/task_service.py`
- `app/api/routes/courses.py`
- `app/api/routes/tasks.py`

**验收**

- 用户可以创建、查询、更新、归档、删除自己的项目。
- 用户不能读取另一个用户的项目。
- 任务可按项目、状态、优先级、标题筛选。
- 分页返回 `total`、`page`、`page_size`、`has_next`。

**重点问题**

- 为什么查询条件里一定要带 `Course.owner_id == current_user.id`？
- 为什么更新任务时不能直接相信请求里的 `task_id`？
- 分页为什么要先查总数，再查当前页？
- `offset = (page - 1) * page_size` 的含义是什么？

**动手实验**

- 增加按截止日期排序。
- 增加“只看逾期任务”查询参数。
- 比较在 Python 中过滤全部任务和用 SQL 过滤的性能差异。

---

### 阶段 7：学习记录与统计

**目标**

- 把多张表组合起来做业务统计。
- 理解 Python 聚合与 SQL 聚合的取舍。

**手敲文件**

- `app/services/study_log_service.py`
- `app/services/stats_service.py`
- `app/api/routes/study_logs.py`
- `app/api/routes/stats.py`

**验收**

- 打卡时可以关联同一项目下的任务。
- 统计能返回今日、本周、累计、连续天数和日趋势。
- 分项目统计返回学习分钟与任务完成率。

**重点问题**

- 如果今天还没打卡，连续天数应该从哪天开始算？
- 为什么统计时仍然要按 `user_id` 过滤？
- 为什么学习记录既保存 `course_id` 又可选保存 `task_id`？

**动手实验**

- 增加“本月学习分钟”。
- 增加“最长连续打卡天数”。
- 把每日趋势改成按周聚合。

---

### 阶段 8：网页界面

**目标**

- 理解浏览器通过 `fetch` 调用 API。
- 理解 Token 存放、请求头、加载状态和错误展示。

**手敲文件**

- `app/static/index.html`
- `app/static/styles.css`
- `app/static/app.js`

**验收**

- 注册后自动登录。
- 创建项目刷新后仍存在。
- 添加任务、打卡、标记完成都能即时反映到统计。
- 退出后 Token 被清除。

**重点问题**

- `FormData` 和 JSON 请求体有什么区别？
- OAuth2 登录为什么要求 `application/x-www-form-urlencoded`？
- 为什么插入用户内容到 HTML 前要转义？
- 401 时前端为什么要清理本地 Token？

**动手实验**

- 给任务增加编辑弹窗。
- 给趋势图增加 tooltip。
- 使用 `localStorage` 之外的方式保存 Token，并比较安全性。

---

### 阶段 9：测试和静态检查

**目标**

- 用测试证明业务规则，而不是只靠手点页面。
- 建立可重复、互不污染的测试数据库。

**手敲文件**

- `tests/conftest.py`
- `tests/test_auth.py`
- `tests/test_courses.py`
- `tests/test_tasks.py`
- `tests/test_logs_and_stats.py`

**命令**

```powershell
uv run pytest -q
uv run ruff check app tests
```

**重点问题**

- 为什么测试使用独立 Engine，而不是项目正式数据库？
- 为什么使用 `StaticPool` 和内存 SQLite？
- 为什么每个测试都需要重新创建表？
- 依赖覆盖 `app.dependency_overrides` 的作用是什么？

**动手实验**

- 增加“删除学习记录”的测试。
- 增加“分页第二页”的测试。
- 增加“归档项目不计入活动项目数”的测试。

---

### 阶段 10：复盘与二次实现

不看参考代码，完成下面任务：

1. 新建一个 `Bookmark` 项目，包含用户、收藏夹、书签三张表。
2. 实现注册、登录和当前用户接口。
3. 实现收藏夹与书签 CRUD。
4. 每个用户只能访问自己的数据。
5. 写 6 个以上接口测试。
6. 画出数据关系图并解释每个外键。
7. 用 5 分钟讲清楚一次请求从 Router 到数据库再返回的完整路径。

能做到这些，说明这个项目已经真正变成你的知识，而不只是仓库里的代码。

## 三、常见错误排查表

| 现象 | 常见原因 | 排查方向 |
| --- | --- | --- |
| 401 Unauthorized | Token 缺失、过期或格式不对 | 检查 `Authorization: Bearer ...` |
| 422 Unprocessable Entity | 请求体字段或类型不符合 Schema | 打开 `/docs` 查看字段定义 |
| 404 但数据明明存在 | 查询条件带了别的 `user_id` | 检查数据隔离条件 |
| MissingGreenlet | 异步中触发隐式懒加载 | 使用 `selectinload` 或显式查询 |
| no such table | 没建表或连了另一个数据库 | 检查启动日志和 `DATABASE_URL` |
| UNIQUE constraint failed | 重复用户名、邮箱或测试数据 | 检查唯一索引和测试隔离 |
| CORS error | 前端域名不在允许列表 | 检查 `CORS_ORIGINS` |
| SQLite 外键不生效 | 没启用 `PRAGMA foreign_keys=ON` | 检查 Engine connect 事件 |

## 四、每次学习后的复盘模板

```markdown
## 2026-11-22 · 认证模块

### 今天完成
- 实现密码哈希
- 实现登录并签发 JWT
- 实现 get_current_user 依赖

### 我今天能解释
- JWT 为什么不需要在服务端保存会话
- 为什么密码哈希不可逆
- 401 和 403 的区别

### 遇到的问题
- Swagger 登录后仍然 401，因为 Token 复制时多了空格

### 明天要做
- 完成项目和任务 CRUD
- 写用户数据隔离测试
```

## 五、进阶方向

完成基础路线后，可以按这个顺序继续：

1. Alembic 迁移
2. 刷新 Token 与登出机制
3. 角色权限
4. 标签和任务排序
5. 学习热力图
6. Docker Compose
7. PostgreSQL
8. Redis 缓存与接口限流
9. 前后端分离
10. 部署与日志监控