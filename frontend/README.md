# AI Incubator Frontend

React + TypeScript 前端应用，提供想法孵化器的完整用户界面。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 7
- **路由**: React Router v7
- **状态管理**: Zustand
- **UI 组件**: Ant Design 6
- **思维导图**: React Flow 11
- **样式**: TailwindCSS 3
- **HTTP 客户端**: Axios
- **测试**: Vitest + React Testing Library

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 默认配置指向本地后端 http://localhost:8000/api
```

### 3. 启动开发服务器
```bash
npm run dev
```

访问 http://localhost:5173

## 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run test` - 运行测试
- `npm run test:ui` - Vitest UI
- `npm run test:coverage` - 测试覆盖率

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 调用封装
│   ├── components/       # 可复用组件
│   │   ├── mindmap/      # 思维导图组件
│   │   └── ui/           # 通用 UI 组件
│   ├── pages/           # 页面组件
│   ├── stores/          # Zustand 状态管理
│   ├── types/           # TypeScript 类型
│   ├── test/            # 测试文件
│   └── App.tsx          # 应用入口
├── public/              # 静态资源
├── index.html
├── vite.config.ts       # Vite 配置
├── tailwind.config.js   # TailwindCSS 配置
└── package.json
```

## 核心功能

### 1. 认证流程
- 登录: `/login`
- 注册: `/register`
- JWT Token 存储在 Zustand store

### 2. 项目管理
- 项目列表: `/projects`
- 创建项目
- 删除项目

### 3. 孵化工作区
- **可视化**: Mind Elixir 渲染通用思维导图
- **对话**: AI 按通用探索流程持续追问
- **节点面板**: 查看节点详情并围绕节点回答

### 4. AI 集成
- 通用问题生成
- 观点提炼
- 追问生成
- 无 API key 时使用确定性 fallback

## 主题定制

### 颜色方案 (淡蓝色主题)
```css
--primary-500: #0073e6
--sky-50: #f0f9ff
--sky-500: #0ea5e9
--sky-600: #0284c7
```

## License
MIT
