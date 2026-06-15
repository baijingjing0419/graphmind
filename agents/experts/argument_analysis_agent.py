"""论证分析专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class ArgumentAnalysisAgent(BaseAgent):
    """论证分析专家 - 拆解复杂问题、明确假设和推理链"""

    def get_default_model(self) -> str:
        return "gpt-oss:20b"

    def get_prompt(self) -> str:
        return """你是论证分析专家，专门拆解复杂问题、明确假设和推理链。

你的任务：
1. 拆解复杂问题为清晰的子命题
2. 识别问题中的假设和前提
3. 构建逻辑推理链
4. 评估论证的有效性和完整性"""

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            other_results = context.get("other_results", []) if context else []
            evidence_ids = []
            for item in other_results:
                evidence_ids.extend(item.get("evidence_ids", []) or [])

            prompt = f"""请对以下问题进行论证分析：

问题：{task}

相关信息：
{self._format_other_results(other_results)}

请提供：
1. 问题的核心命题拆解
2. 隐含的假设和前提识别
3. 逻辑推理链的构建
4. 论证的有效性评估
5. 潜在的逻辑漏洞或改进建议"""

            result = ""
            async for chunk in self._call_llm(prompt=self.merge_system_into_task_prompt(prompt), stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "argument_analysis"
                    }

            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "argument_analysis",
                    "evidence_ids": list(dict.fromkeys(evidence_ids)),
                    "claims": [{
                        "source_agent": "argument_analysis",
                        "content": result[:240],
                        "status": "synthesized",
                    }],
                    "confidence": 0.88
                }

        except Exception as e:
            logger.error(f"ArgumentAnalysisAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"论证分析失败: {str(e)}",
                "agent_type": "argument_analysis"
            }

    def _format_other_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "暂无其他信息"

        formatted = []
        for result in results:
            agent_type = result.get("agent_type", "unknown")
            content = result.get("content", "")
            formatted.append(f"[{agent_type}]: {content[:500]}")

        return "\n\n".join(formatted)
