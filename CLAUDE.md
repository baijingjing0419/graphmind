# GraphMind 专属自定义技能 (Custom Skills)

## 1. 文档解析测试器 (test-parser)
- **触发场景**：当你需要我验证或测试 `parsers` 目录下的解析逻辑时。
- **执行动作**：请自动寻找或编写一个临时的 Python 脚本加载特定的 parser（如 `pdf_parser` 或 `markdown_parser`），并读取用户指定的文件进行解析，最后在终端输出解析出的文本内容和 Chunking 结果。
- **关联组件**：优先调用 `parsers/parser_factory.py` 来实例化对应的解析器。
## 2. RAG 质量检测 (run-rag-eval)
- **触发场景**：当我修改了 `retrieval/` 目录下的检索逻辑或 `embedding/` 目录下的逻辑，或者当你要求我“评估检索质量”时。
- **执行动作**：请自动在终端运行相关的评估脚本，例如执行 `python eval/evaluate.py` 或 `python eval/ragas_eval.py`，并使用默认的测试集（如 `eval/retrieval_dataset.demo.json`），最后为用户总结本次修改对召回率/准确率的影响。
## 3. 智能体链路追踪 (agent-trace)
- **触发场景**：当我需要理解多智能体的工作流状态，或者排查 `agents/workflow` 和 `agents/coordinator` 相关的调度逻辑和死锁/卡顿问题时。
- **执行动作**：请主动查阅 `logs/` 目录下的最新日志文件，或者编写简单的调试代码接入 `agent_workflow.py`，提取出 Coordinator 与各个 Expert Agents 之间的对话历史、任务分发路径和中间态 Scratchpad 并在终端打印，帮助用户分析执行链路。