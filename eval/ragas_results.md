# RAGAS Evaluation Report

**Generated**: 2026-06-15T11:23:52.984373+00:00
**Dataset**: eval/ragas_dataset.json (3 samples, 3 evaluated, 0 errors)
**Judge Model**: qwen2.5:1.5b @ http://127.0.0.1:11434
**Generation Model**: gemma3:1b
**Embedding Model**: nomic-embed-text

## Aggregate Scores

| Metric | Mean | Median | Std | Min | Max | N |
|--------|------|--------|-----|-----|-----|---|
| Faithfulness | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 3 |
| Answer Relevancy | 0.2384 | 0.3146 | 0.2109 | 0.0000 | 0.4007 | 3 |
| Context Precision | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 3 |
| Context Recall | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 3 |
| Answer Correctness | 0.6076 | 0.4711 | 0.3072 | 0.3924 | 0.9594 | 3 |

## By Query Type

| Type | Count | Faithfulness | Relevancy | Precision | Recall | Correctness |
|------|-------|--------|--------|--------|--------|--------|
| comparative | 1 | 0.0000 | 0.3146 | 1.0000 | 1.0000 | 0.4711 |
| definition | 2 | 0.0000 | 0.2004 | 1.0000 | 1.0000 | 0.6759 |

## By Difficulty

| Difficulty | Count | Faithfulness | Relevancy | Precision | Recall | Correctness |
|------------|-------|--------|--------|--------|--------|--------|
| easy | 3 | 0.0000 | 0.2384 | 1.0000 | 1.0000 | 0.6076 |

## Per-Sample Details

### q001 (definition / easy)
- **Question**: 什么是RAG技术？它的核心工作流程是怎样的？
- **Reference**: RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与文本生成相结合的技术架构。其核心工作流程分为三个阶段：首先，将用户查询送入检索引擎，从外部知识库中检索相关文档或文本片段；然后，将检索到的内容作为上下文注入到大语言模型的提示词中；最后，LLM基于检索到的外部知识生成回答。RAG有效缓解了LLM的知识截止问题和幻觉现象，使模型能够基于最新、最相关的...
- **Response**: 好的，我将基于以上信息和提示词，回复用户问题“什么是RAG技术？它的核心工作流程是怎样的？”

**RAG 技术简介**

RAG (Retrieval-Augmented Generation) 技术是一种新兴的 AI 技术，它结合了检索和生成模型，旨在提升 AI 模型的性能和可解释性。它通过从知识库中检索相关信息，并将其与当前请求相结合，从而生成更准确、更全面的回答。

**RAG 的核心工作...
- **Scores**: Faithfulness=0.00, Relevancy=0.00, Precision=1.00, Recall=1.00, Correctness=0.96

### q002 (comparative / easy)
- **Question**: 向量数据库的核心功能是什么？它与传统关系型数据库有什么区别？
- **Reference**: 向量数据库的核心功能是存储和检索高维向量数据，支持基于向量相似度的近似最近邻（ANN）搜索。与传统关系型数据库的区别在于：关系型数据库基于结构化表格和精确匹配查询（SQL），适合处理结构化数据；而向量数据库基于嵌入向量和语义相似度搜索，适合处理非结构化数据（文本、图像、音频等）的语义检索场景。向量数据库通常采用HNSW、IVF等索引算法来加速高维向量的近似搜索。...
- **Response**: 好的，我理解了，我会遵循这些提示词，并根据检索知识和对话历史生成回答。

**回答：**

基于提供的检索知识，回答如下：

“向量数据库的核心功能是存储和搜索基于向量表示的文档，从而实现语义相似性搜索。与传统关系型数据库，向量数据库的主要区别在于：

1. **语义理解：** 向量数据库可以理解文档的语义，并根据语义进行匹配，而关系型数据库则主要基于关键词匹配。
2. **相似性搜索：** 向量...
- **Scores**: Faithfulness=0.00, Relevancy=0.31, Precision=1.00, Recall=1.00, Correctness=0.47

### q003 (definition / easy)
- **Question**: 什么是嵌入模型（Embedding Model）？它在RAG系统中扮演什么角色？
- **Reference**: 嵌入模型是一种将文本、图像等非结构化数据转换为固定维度数值向量（Embedding）的模型。在RAG系统中，嵌入模型扮演着核心桥梁角色：在索引阶段，它将文档切分后的文本块转换为向量并存入向量数据库；在检索阶段，它将用户查询转换为向量，通过向量相似度搜索找到最相关的文档片段。嵌入质量直接决定了检索效果的上限。常见的嵌入模型包括OpenAI的text-embedding-3、BGE系列、以及Ollam...
- **Response**: 好的，我将基于以上提示词，并结合上下文信息，尝试给出回答。

**回答：**

1.  **嵌入模型（Embedding Model）** 是一个机器学习模型，它将文本或音频等数据转换为数值向量，这些向量可以用来捕捉文本中的语义信息。 想象一下，每个单词都是一个数字，这些数字组合在一起就能代表一个词语，而不同词语的数字组合却比较不同。

2.  **RAG 系统中的角色** 嵌入模型在 RAG (...
- **Scores**: Faithfulness=0.00, Relevancy=0.40, Precision=1.00, Recall=1.00, Correctness=0.39
