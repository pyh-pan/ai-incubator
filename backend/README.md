# AI Incubator Backend API

FastAPI 后端服务，提供用户认证、项目管理、思维导图节点管理和 AI 智能功能。

## 技术栈

- **框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **AI 集成**: OpenAI API
- **认证**: JWT (python-jose)
- **测试**: pytest + pytest-asyncio

## 快速开始

### 1. 环境准备

```bash
# 安装 Python 3.11+
python --version

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际配置
# 必填项：
# - DATABASE_URL: PostgreSQL 连接字符串
# - SECRET_KEY: JWT 密钥（生产环境必须修改）
# - OPENAI_API_KEY: OpenAI API 密钥
```

### 3. 数据库迁移

```bash
# 运行数据库迁移
alembic upgrade head

# 或使用 Flask 命令（如果集成了）
python -m alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 验证服务

访问 http://localhost:8000/docs 查看 API 文档

## API 端点

### 认证 `/api/auth`
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户

### 项目 `/api/projects`
- `POST /` - 创建项目
- `GET /` - 获取项目列表
- `GET /{id}` - 获取项目详情
- `PUT /{id}` - 更新项目
- `DELETE /{id}` - 删除项目
- `GET /{id}/mindmap` - 获取思维导图

### 节点 `/api/nodes`
- `POST /` - 创建节点
- `GET /{id}` - 获取节点
- `PUT /{id}` - 更新节点
- `DELETE /{id}` - 删除节点
- `GET /{id}/children` - 获取子节点

### AI `/api/ai`
- `POST /recommend-framework` - 推荐框架
- `POST /generate-question` - 生成问题
- `POST /extract-points` - 提炼观点
- `POST /followup/{id}` - 生成追问

## 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试文件
pytest tests/test_auth.py

# 查看覆盖率报告
open htmlcov/index.html
```

## 项目结构

```
backend/
├── app/
│   ├── api/            # API 路由
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── nodes.py
│   │   └── ai.py
│   ├── core/           # 核心配置
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/         # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── project.py
│   │   └── node.py
│   ├── schemas/        # Pydantic schemas
│   │   ├── user.py
│   │   ├── project.py
│   │   └── node.py
│   ├── services/       # 业务逻辑
│   │   └── ai_service.py
│   └── main.py         # FastAPI 入口
├── alembic/           # 数据库迁移
│   └── versions/
├── tests/             # 测试文件
│   ├── test_auth.py
│   └── test_ai_service.py
├── requirements.txt
├── pyproject.toml
└── pytest.ini
```

## 数据库模型

### Users (用户表)
- id: UUID
- email: 唯一邮箱
- username: 用户名
- hashed_password: 加密密码
- created_at, updated_at

### Projects (项目表)
- id: UUID
- user_id: 用户ID (外键)
- title: 项目标题
- framework: 思维框架
- status: active/archived
- created_at, updated_at

### MindmapNodes (思维导图节点表)
- id: UUID
- project_id: 项目ID (外键)
- parent_id: 父节点ID (外键，可为空)
- label: 节点标签
- question: AI 问题
- context: 背景信息
- answer: 用户回答
- extracted_points: 提炼观点 (JSON)
- status: unanswered/in_progress/answered
- depth: 节点深度
- position: 位置坐标 (JSON)
- created_at, updated_at

### ConversationHistory (对话历史表)
- id: UUID
- project_id: 项目ID (外键)
- node_id: 节点ID (外键)
- role: user/assistant
- content: 对话内容
- metadata: 元数据 (JSON)
- created_at

### EvolutionHistory (演化历史表)
- id: UUID
- node_id: 节点ID (外键)
- old_answer: 旧回答
- new_answer: 新回答
- change_summary: 变化摘要
- created_at

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/` 创建路由文件
2. 在 `app/schemas/` 添加 Pydantic models
3. 在 `app/models/` 添加 SQLAlchemy models (如需新表)
4. 在 `app/main.py` 注册路由
5. 编写测试

### 添加新的 AI 功能

1. 在 `app/services/ai_service.py` 添加方法
2. 在 `app/api/ai.py` 添加端点
3. 更新 schemas
4. 编写测试

## 部署

### Docker

```bash
# 构建镜像
docker build -t ai-incubator-backend .

# 运行容器
docker run -p 8000:8000 --env-file .env ai-incubator-backend
```

### 环境变量

生产环境必填：
- `DATABASE_URL`: PostgreSQL 连接
- `SECRET_KEY`: 强随机密钥
- `OPENAI_API_KEY`: OpenAI API 密钥
- `CORS_ORIGINS`: 允许的前端域名

## License

MIT
