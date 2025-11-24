# 前后端分离架构说明

## 架构概览

本项目采用前后端分离架构：

- **后端（FastAPI）**：提供 RESTful API 服务
- **前端（React + Vite）**：提供现代化的用户界面

## 目录结构

```
FastAPI-Boilerplate/
├── app/                    # 后端代码
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── static/            # 静态资源（仅用于存放文件，不提供登录页面）
├── web/                    # 前端代码
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   │   ├── Login.tsx  # 登录页面 ✅
│   │   │   ├── Register.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── components/    # UI 组件
│   │   └── lib/           # 工具库
│   ├── .env.example       # 前端环境变量示例
│   └── vite.config.ts     # Vite 配置
└── .env.example           # 后端环境变量示例
```

## 开发环境配置

### 1. 后端配置

#### 环境变量（`.env`）

```bash
# 服务器配置
SERVER_HOST=localhost
SERVER_PORT=8000

# 数据库配置
POSTGRES_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DATABASE=0

# JWT 配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# OAuth 配置（可选）
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

#### 启动后端服务

```bash
# 安装依赖
uv sync

# 启动数据库和 Redis
docker-compose up -d

# 运行数据库迁移
make migrate

# 启动后端服务（默认 http://localhost:8000）
make run
# 或
uv run python main.py
```

后端服务将运行在 `http://localhost:8000`，提供以下端点：

- API 文档：`http://localhost:8000/docs`
- API 端点：`http://localhost:8000/v1/*`

### 2. 前端配置

#### 环境变量（`web/.env`）

```bash
# 后端 API 地址
VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### 启动前端服务

```bash
# 进入前端目录
cd web

# 安装依赖
npm install
# 或
pnpm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
# 或
pnpm dev
```

前端服务将运行在 `http://localhost:5173`（Vite 默认端口）

## 开发流程

### 同时运行前后端

**终端 1 - 后端：**
```bash
# 在项目根目录
make run
```

**终端 2 - 前端：**
```bash
# 在 web 目录
cd web
npm run dev
```

### 访问应用

1. 打开浏览器访问：`http://localhost:5173`
2. 前端会自动代理 `/api` 请求到后端 `http://localhost:8000`
3. 登录页面位于：`http://localhost:5173/login`

## API 代理配置

前端通过 Vite 配置的代理将 API 请求转发到后端：

```typescript
// web/vite.config.ts
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

  return {
    server: {
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
        },
      },
    },
  }
})
```

这意味着：
- 前端请求 `/api/v1/users/login` 
- 实际请求 `http://localhost:8000/api/v1/users/login`

## 生产环境部署

### 方案 1：分离部署（推荐）

**后端：**
```bash
# 构建后端
docker build -t fastapi-backend .

# 运行后端容器
docker run -p 8000:8000 fastapi-backend
```

**前端：**
```bash
# 构建前端
cd web
npm run build

# 部署 dist 目录到 CDN 或静态服务器
# 例如：Vercel, Netlify, AWS S3 + CloudFront
```

### 方案 2：统一部署

将前端构建产物放到后端静态目录：

```bash
# 构建前端
cd web
npm run build

# 复制到后端静态目录
cp -r dist/* ../app/static/

# 配置后端提供前端页面
# 在 app/core/register.py 中添加 SPA 路由处理
```

## 端口配置

### 修改后端端口

在 `.env` 文件中：
```bash
SERVER_PORT=9000
```

### 修改前端 API 地址

在 `web/.env` 文件中：
```bash
VITE_API_BASE_URL=http://127.0.0.1:9000
```

### 修改前端开发服务器端口

在 `web/vite.config.ts` 中：
```typescript
export default defineConfig({
  server: {
    port: 3000,  // 自定义端口
    proxy: { /* ... */ }
  }
})
```

## 常见问题

### 1. CORS 错误

确保后端已启用 CORS 中间件（默认已启用）：

```python
# app/core/register.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. API 请求 404

检查：
- 后端服务是否正常运行
- API 路径是否正确（应以 `/api/v1/` 开头）
- Vite 代理配置是否正确

### 3. 登录后跳转失败

检查：
- Token 是否正确保存到 localStorage
- 路由配置是否正确
- 认证中间件是否正常工作

## 技术栈

### 后端
- **FastAPI** - 现代 Python Web 框架
- **SQLAlchemy** - ORM
- **PostgreSQL** - 数据库
- **Redis** - 缓存
- **JWT** - 认证

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Axios** - HTTP 客户端

## 下一步

1. ✅ 前后端分离架构已配置完成
2. ✅ 使用 `web/src/pages/Login.tsx` 作为登录页面
3. ✅ 后端仅提供 API 服务
4. 建议：配置生产环境的部署流程
5. 建议：添加前端单元测试和 E2E 测试

