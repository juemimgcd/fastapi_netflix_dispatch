# fastapi_netflix_dispatch

一个面向简历/学习场景的 `Netflix Dispatch` 精简版后端实现，基于 `FastAPI + SQLAlchemy + Alembic + Redis + Celery`。

## 项目目标

- 复刻 Incident 管理核心流程，不追求全量功能。
- 强调后端工程化实践：权限、状态流转、通知、迁移、容器化、测试、CI。

## 已实现能力

- 用户认证：注册、登录、JWT 鉴权、管理员权限校验
- Incident：创建、列表、详情、搜索、指派、状态流转
- Team/RBAC：团队、成员管理、可见性规则
- Task：任务创建、指派、状态更新、我的任务
- Timeline/Comment：事件流与评论能力
- Notification：站内通知读写接口
- WebSocket：实时通知订阅通道

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x (async) + asyncpg
- Alembic
- Redis
- Celery
- PostgreSQL

## 目录结构

```text
.
├── conf/         # 配置与数据库会话
├── models/       # SQLAlchemy 模型
├── schemas/      # Pydantic 请求/响应模型
├── crud/         # 数据库读写层
├── services/     # 业务编排层
├── routers/      # API 路由层
├── utils/        # 公共工具（鉴权、缓存、ws、邮件等）
├── alembic/      # 数据库迁移
└── main.py       # FastAPI 应用入口
```

## 本地启动

1. 创建并激活虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. 安装依赖

```powershell
pip install -r requirements.txt
```

3. 配置环境变量

- 复制 `.env.example` 为 `.env`（或使用 `.venv/.env`）
- 至少保证 `ASYNC_DATABASE_URL / REDIS_URL / JWT_SECRET` 有值

4. 执行迁移

```powershell
alembic upgrade head
```

5. 启动 API

```powershell
uvicorn main:app --reload
```

打开文档：`http://127.0.0.1:8000/docs`

## Docker Compose 一键启动

```powershell
docker compose up --build
```

启动后：

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## 测试

```powershell
pip install -r requirements-dev.txt
pytest -q
```

当前提供最小可运行测试（健康检查与基础路由），后续可继续补充鉴权、权限和状态流转场景测试。

## CI

仓库内置 GitHub Actions 工作流（`.github/workflows/ci.yml`）：

- 安装依赖
- 执行 `pytest -q`

## 简历可写点（建议）

- 设计并实现 Incident 全链路后端：事件、任务、通知、团队权限
- 使用 SQLAlchemy Async + Alembic 管理可演进数据模型
- 通过 Redis + WebSocket 支撑实时通知能力
- 完成 Docker 化与 CI，具备可复现与可验证交付能力

