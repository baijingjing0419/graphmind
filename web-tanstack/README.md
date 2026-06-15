# GraphMind Frontend

基于 Vite + TanStack 系列的现代化前端，接入 GraphMind FastAPI 后端。

## 技术栈

- React 19
- Vite 8
- TypeScript 6
- TanStack Router / Query / Table / Virtual
- Tailwind CSS v4
- shadcn/ui
- Zustand
- Monaco Editor
- xterm.js
- React Flow

## 启动方式

确保后端运行在 `http://localhost:8000`：

```bash
cd web-tanstack
npm install
npm run dev
```

默认访问 `http://localhost:5173`。

## 环境变量

```bash
VITE_API_URL=http://localhost:8000
```

## 目录结构

```txt
web-tanstack/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   ├── documents/
│   │   ├── settings/
│   │   ├── shell/
│   │   └── ui/
│   ├── lib/
│   ├── stores/
│   ├── types/
│   ├── index.css
│   ├── main.tsx
│   └── router.tsx
├── components.json
└── vite.config.ts
```
