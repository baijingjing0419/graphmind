# GraphMind

融合知识图谱的多智能体深度研究系统。基于 FastAPI 构建，支持文档入库、混合检索（向量 + 关键词 + 知识图谱）、流式对话、多 Agent 协作深度研究。

## 核心能力

- **RAG 问答**：混合检索增强生成，向量检索 + BM25 关键词检索 + Neo4j 知识图谱关联检索，自动融合排序
- **文档管理**：支持 PDF、Word、Markdown、TXT 等常见文档上传、解析、分块、嵌入、入库及处理进度追踪
- **知识空间**：多知识库隔离，支持创建、列表、关联检索
- **深度研究**：多 Agent 协作分析复杂问题，包含协调器、检索、代码分析、公式分析、概念解释、示例生成、批判评估等专家 Agent
- **运行时配置**：模型、Agent、HTTP 日志等运行时参数可通过 API 动态调整
- **健康监控**：liveness / readiness / 依赖状态 / 基础系统指标
- **质量评测**：基于 Ragas 框架的量化评测体系，覆盖忠实度、回答相关性、上下文精确率/召回率、答案正确性五个维度，支持结构化报告输出

## 技术栈

- **后端**：FastAPI + Uvicorn
- **向量库**：Qdrant（gRPC 连接，支持高并发）
- **图数据库**：Neo4j（知识图谱构建与关联检索）
- **文档库**：MongoDB（会话、文档元数据、配置）
- **缓存**：Redis
- **模型**：Ollama 本地大模型与嵌入模型
- **文档处理**：PyMuPDF、PyPDF2、python-docx、Unstructured、PaddleOCR
- **文本处理**：LangChain、jieba、sentence-transformers
- **评测**：Ragas（RAG 质量评估框架）

## 快速开始

### 1. 环境要求

- Docker / Docker Compose
- Ollama（本地模型服务）

### 2. 配置环境变量

```bash
cp .env.example .env.docker
# 编辑 .env.docker，按需修改配置
```

### 3. 拉取 Ollama 模型

```bash
ollama pull gemma3:1b
ollama pull nomic-embed-text
ollama pull qwen2.5:3b         # Ragas 评测用 Judge 模型
```

### 4. 一键启动

```bash
docker compose up -d
```

启动全部服务：MongoDB、Qdrant、Neo4j、Redis、后端 API、前端。

| 服务 | 地址 |
| --- | --- |
| 前端页面 | `http://localhost` |
| API 文档 | `http://localhost:8000/docs` |
| 健康检查 | `http://localhost:8000/health` |

## 主要 API

| 模块 | 端点 | 说明 |
| --- | --- | --- |
| 聊天 | `POST /api/chat` | RAG 增强对话，SSE 流式返回 |
| 深度研究 | `POST /api/chat/deep-research` | 多 Agent 协作深度研究 |
| 会话 | `GET/POST /api/chat/conversations` | 会话列表与创建 |
| 文档 | `POST /api/documents/upload` | 上传文档入库 |
| 知识空间 | `GET/POST /api/knowledge-spaces` | 知识空间管理 |
| 检索 | `POST /api/retrieval` | 混合检索（含证据追踪） |
| 设置 | `GET/PUT /api/settings/runtime` | 运行时配置 |
| 健康 | `GET /health` | 系统健康与依赖状态 |

## 质量评测

基于 [Ragas](https://github.com/explodinggradients/ragas) 框架的端到端 RAG 质量评测体系，覆盖 **检索质量** 和 **生成质量** 五个维度：

| 指标 | 衡量维度 | 说明 |
| --- | --- | --- |
| Faithfulness | 忠实度 | 回答是否可追溯到检索上下文（幻觉检测） |
| Answer Relevancy | 回答相关性 | 回答是否切题 |
| Context Precision | 上下文精确率 | 检索结果是否相关且排序合理 |
| Context Recall | 上下文召回率 | 检索是否覆盖回答所需的全部信息 |
| Answer Correctness | 答案正确性 | 回答与标准答案的事实一致性 |

### 数据集

40 个中文评测用例位于 `eval/ragas_dataset.json`，覆盖 7 种题型（事实查找、概念定义、对比分析、多跳推理、分析推理、步骤流程、边界情况）× 3 档难度。

### 运行评测

```bash
# 全量评测（需先上传文档到知识库）
make eval-ragas

# 快速验证（前 5 条）
make eval-ragas-quick

# 自定义 Judge 模型
python eval/ragas_eval.py --judge-model qwen2.5:7b --limit 10

# 跳过流水线重跑打分（使用缓存）
python eval/ragas_eval.py --skip-generation
```

评测完成后生成两个报告：
- `eval/ragas_results.json` — 结构化数据（含聚合统计、分组统计、逐题详情）
- `eval/ragas_results.md` — 可读 Markdown 报告

## 目录结构

```txt
graphmind/
├── agents/              # 多智能体协作系统
│   ├── base/            # Agent 基类
│   ├── coordinator/     # 协调器 Agent
│   ├── experts/         # 专家 Agent（检索、代码、公式、批判等）
│   ├── workflow/        # Agent 工作流编排
│   └── tools/           # Agent 工具集
├── chunking/            # 文本分块策略
├── database/            # MongoDB、Qdrant 连接与仓储
├── embedding/           # 嵌入服务
├── eval/                # 评测工具
├── middleware/           # FastAPI 中间件
├── models/              # 数据模型
├── parsers/             # 文档解析器
├── retrieval/           # 查询分析、检索与重排
├── routers/             # API 路由
├── scripts/             # 运维与迁移脚本
├── services/            # 业务服务层
├── utils/               # 日志、监控、通用工具
├── web-tanstack/        # Vite + TanStack 前端
├── main.py              # 应用入口
├── docker-compose.yml   # 本地依赖服务
└── Dockerfile           # API 镜像构建
```

## License

MIT
