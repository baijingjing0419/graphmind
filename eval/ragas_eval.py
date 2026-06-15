"""
Ragas-based evaluation for the GraphMind RAG pipeline.

Evaluates end-to-end RAG quality using 5 Ragas metrics:
  - Faithfulness (hallucination detection)
  - ResponseRelevancy (answer relevance to question)
  - LLMContextPrecisionWithReference (retrieval precision + ranking)
  - LLMContextRecall (retrieval completeness)
  - AnswerCorrectness (factual correctness vs ground truth)

Uses Ollama local models as the judge LLM and embedding provider.

Usage:
    python eval/ragas_eval.py                          # Full evaluation
    python eval/ragas_eval.py --limit 5                 # Quick test
    python eval/ragas_eval.py --judge-model qwen2.5:7b # Different judge model
    python eval/ragas_eval.py --skip-generation         # Re-score cached results
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import rag_service
from services.ollama_service import OllamaService
from utils.logger import logger

# ── Constants ──────────────────────────────────────────────────────────
DEFAULT_DATASET = "eval/ragas_dataset.json"
DEFAULT_OUTPUT = "eval/ragas_results"
DEFAULT_JUDGE_MODEL = "qwen2.5:3b"
CACHE_FILE = "eval/.ragas_cache.json"


class RagasEvaluator:
    """Encapsulates the full Ragas evaluation lifecycle."""

    def __init__(
        self,
        judge_model: str = DEFAULT_JUDGE_MODEL,
        ollama_base_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        self.judge_model = judge_model
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
        )
        self.embedding_model = embedding_model or os.getenv(
            "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"
        )

        # Service instances for pipeline execution (generation model from env)
        self.ollama_service = OllamaService(
            base_url=self.ollama_base_url,
        )

        # Judge components — initialized lazily
        self._judge_llm = None
        self._judge_embeddings = None
        self._metrics = None

    @property
    def judge_llm(self):
        if self._judge_llm is None:
            from openai import AsyncOpenAI
            from ragas.llms import llm_factory

            ollama_client = AsyncOpenAI(
                base_url=f"{self.ollama_base_url}/v1",
                api_key="ollama",
            )
            self._judge_llm = llm_factory(
                self.judge_model,
                client=ollama_client,
                temperature=0.0,
                max_tokens=1024,
            )
        return self._judge_llm

    @property
    def judge_embeddings(self):
        if self._judge_embeddings is None:
            from openai import AsyncOpenAI
            from ragas.embeddings import embedding_factory

            ollama_client = AsyncOpenAI(
                base_url=f"{self.ollama_base_url}/v1",
                api_key="ollama",
            )
            self._judge_embeddings = embedding_factory(
                "openai",
                model=self.embedding_model,
                client=ollama_client,
                interface="modern",
            )
        return self._judge_embeddings

    @property
    def metrics(self):
        if self._metrics is None:
            from ragas.metrics.collections import (
                Faithfulness,
                AnswerRelevancy,
                ContextPrecisionWithReference,
                ContextRecall,
                AnswerCorrectness,
            )

            self._metrics = [
                Faithfulness(llm=self.judge_llm),
                AnswerRelevancy(
                    llm=self.judge_llm,
                    embeddings=self.judge_embeddings,
                ),
                ContextPrecisionWithReference(llm=self.judge_llm),
                ContextRecall(llm=self.judge_llm),
                AnswerCorrectness(
                    llm=self.judge_llm,
                    embeddings=self.judge_embeddings,
                ),
            ]
        return self._metrics

    # ── Dataset ──────────────────────────────────────────────────────

    @staticmethod
    def load_dataset(path: str) -> List[Dict[str, Any]]:
        project_root = Path(__file__).resolve().parent.parent
        full_path = project_root / path
        if not full_path.exists():
            raise FileNotFoundError(f"Dataset not found: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── Pipeline ─────────────────────────────────────────────────────

    async def run_pipeline(self, question: str) -> Dict[str, Any]:
        """Execute retrieval + generation, returning contexts and answer."""
        result = await rag_service.retrieve_context(question)
        context_text = result.get("context", "")
        evidence = result.get("evidence", [])

        retrieved_contexts = [
            item.get("text", "")
            for item in evidence
            if isinstance(item, dict) and item.get("text", "").strip()
        ]

        # Fallback: if no evidence list, use the full context string
        if not retrieved_contexts and context_text.strip():
            retrieved_contexts = [context_text]

        generated_answer = ""
        try:
            async for chunk in self.ollama_service.generate(
                question, context=context_text, stream=False
            ):
                generated_answer += chunk
        except Exception as e:
            logger.error(f"Generation failed for '{question[:40]}...': {e}")
            generated_answer = "[Generation Error]"

        return {
            "answer": generated_answer,
            "contexts": retrieved_contexts,
            "context_full": context_text,
        }

    # ── Evaluation ───────────────────────────────────────────────────

    async def evaluate(
        self,
        dataset: List[Dict[str, Any]],
        limit: int = 0,
        skip_generation: bool = False,
    ) -> Dict[str, Any]:
        """Run pipeline for each question, then score with Ragas."""
        if limit > 0:
            dataset = dataset[:limit]

        # Load or initialize cache
        cache = self._load_cache() if skip_generation else {}

        evaluated_count = 0
        pipeline_results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        total = len(dataset)
        print(f"\n{'='*60}")
        print(f"Ragas Evaluation — {total} samples")
        print(f"  Judge LLM: {self.judge_model}")
        print(f"  Generation LLM: {self.ollama_service.model_name}")
        print(f"  Embedding: {self.embedding_model}")
        print(f"{'='*60}\n")

        for i, item in enumerate(dataset):
            qid = item.get("id", f"q{i:03d}")
            question = item["question"]
            reference = item.get("reference", "")
            query_type = item.get("query_type", "unknown")
            difficulty = item.get("difficulty", "unknown")
            short_q = question[:60] + ("..." if len(question) > 60 else "")

            print(f"[{i+1}/{total}] {short_q}", end=" ", flush=True)

            # ── Pipeline Execution ──
            cache_key = qid

            if skip_generation and cache_key in cache:
                pipe = cache[cache_key]
            else:
                try:
                    pipe = await self.run_pipeline(question)
                except Exception as e:
                    logger.error(f"Pipeline error [{qid}]: {e}")
                    errors.append({"id": qid, "stage": "pipeline", "error": str(e)})
                    print("→ PIPELINE ERROR")
                    continue
                cache[cache_key] = pipe

            answer = pipe["answer"]
            contexts = pipe["contexts"]

            if not answer or answer == "[Generation Error]":
                errors.append({"id": qid, "stage": "generation", "error": "empty or error answer"})
                print("→ GEN ERROR")
                pipeline_results.append({
                    "id": qid, "question": question, "reference": reference,
                    "response": answer, "retrieved_contexts": contexts,
                    "query_type": query_type, "difficulty": difficulty,
                    "scores": {}, "error": "generation failed",
                })
                continue

            # ── Build scoring kwargs per metric ──
            metric_kwargs = {
                "faithfulness": {
                    "user_input": question,
                    "response": answer,
                    "retrieved_contexts": contexts,
                },
                "answer_relevancy": {
                    "user_input": question,
                    "response": answer,
                },
                "context_precision_with_reference": {
                    "user_input": question,
                    "reference": reference,
                    "retrieved_contexts": contexts,
                },
                "context_recall": {
                    "user_input": question,
                    "retrieved_contexts": contexts,
                    "reference": reference,
                },
                "answer_correctness": {
                    "user_input": question,
                    "response": answer,
                    "reference": reference,
                },
            }

            # ── Score this single sample ──
            scores: Dict[str, float] = {}
            for metric in self.metrics:
                metric_name = metric.name
                kwargs = metric_kwargs.get(metric_name, {})
                try:
                    result = await metric.ascore(**kwargs)
                    scores[metric_name] = round(float(result.value), 4)
                except Exception as e:
                    logger.error(f"Metric {metric_name} failed [{qid}]: {e}")
                    scores[metric_name] = float("nan")

            pipeline_results.append({
                "id": qid,
                "question": question,
                "reference": reference,
                "response": answer,
                "retrieved_contexts": contexts,
                "query_type": query_type,
                "difficulty": difficulty,
                "scores": scores,
                "error": None,
            })
            evaluated_count += 1

            # Compact per-sample output
            score_parts = []
            for k, v in scores.items():
                short_name = {
                    "faithfulness": "Faith",
                    "answer_relevancy": "Relev",
                    "context_precision_with_reference": "CtxPrec",
                    "context_recall": "CtxRec",
                    "answer_correctness": "Correct",
                }.get(k, k[:8])
                score_parts.append(f"{short_name}={v:.2f}" if not (isinstance(v, float) and v != v) else f"{short_name}=NaN")
            print("→ " + " ".join(score_parts))

        # Save updated cache
        self._save_cache(cache)

        # ── Aggregate ──
        metric_names = [m.name for m in self.metrics]
        aggregate = self._compute_aggregate(pipeline_results, metric_names)
        by_type = self._groupby(pipeline_results, "query_type", metric_names)
        by_difficulty = self._groupby(pipeline_results, "difficulty", metric_names)

        return {
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dataset_path": DEFAULT_DATASET,
                "num_samples": total,
                "num_evaluated": evaluated_count,
                "num_errors": len(errors),
                "judge_model": self.judge_model,
                "judge_base_url": self.ollama_base_url,
                "embedding_model": self.embedding_model,
                "generation_model": self.ollama_service.model_name,
            },
            "aggregate": aggregate,
            "by_query_type": by_type,
            "by_difficulty": by_difficulty,
            "samples": pipeline_results,
            "errors": errors,
        }

    # ── Statistics ────────────────────────────────────────────────────

    @staticmethod
    def _compute_aggregate(
        results: List[Dict], metric_names: List[str]
    ) -> Dict[str, Any]:
        agg: Dict[str, Any] = {}
        for m in metric_names:
            vals = [
                r["scores"].get(m, float("nan"))
                for r in results
                if r.get("scores") and m in r["scores"]
            ]
            clean = [v for v in vals if not (isinstance(v, float) and v != v)]
            if clean:
                agg[m] = {
                    "mean": round(statistics.mean(clean), 4),
                    "median": round(statistics.median(clean), 4),
                    "std": round(statistics.stdev(clean), 4) if len(clean) > 1 else 0.0,
                    "min": round(min(clean), 4),
                    "max": round(max(clean), 4),
                    "count": len(clean),
                }
            else:
                agg[m] = {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        return agg

    @staticmethod
    def _groupby(
        results: List[Dict], key: str, metric_names: List[str]
    ) -> List[Dict[str, Any]]:
        groups: Dict[str, List[Dict]] = {}
        for r in results:
            group = r.get(key, "unknown")
            groups.setdefault(group, []).append(r)

        output = []
        for group, items in sorted(groups.items()):
            entry: Dict[str, Any] = {"group": group, "count": len(items)}
            for m in metric_names:
                vals = [
                    it["scores"].get(m, float("nan"))
                    for it in items
                    if it.get("scores") and m in it["scores"]
                ]
                clean = [v for v in vals if not (isinstance(v, float) and v != v)]
                if clean:
                    entry[f"{m}_mean"] = round(statistics.mean(clean), 4)
                else:
                    entry[f"{m}_mean"] = 0.0
            output.append(entry)
        return output

    # ── Cache ─────────────────────────────────────────────────────────

    def _load_cache(self) -> Dict[str, Any]:
        project_root = Path(__file__).resolve().parent.parent
        path = project_root / CACHE_FILE
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self, data: Dict[str, Any]) -> None:
        project_root = Path(__file__).resolve().parent.parent
        path = project_root / CACHE_FILE
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── Reporting ─────────────────────────────────────────────────────

    @staticmethod
    def generate_report(results: Dict[str, Any], output_prefix: str) -> None:
        project_root = Path(__file__).resolve().parent.parent

        # JSON report
        json_path = project_root / f"{output_prefix}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nJSON report saved to: {json_path}")

        # Markdown report
        md_path = project_root / f"{output_prefix}.md"
        md = RagasEvaluator._to_markdown(results)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Markdown report saved to: {md_path}")

    @staticmethod
    def _to_markdown(results: Dict[str, Any]) -> str:
        meta = results["meta"]
        agg = results["aggregate"]
        by_type = results.get("by_query_type", [])
        by_diff = results.get("by_difficulty", [])
        samples = results.get("samples", [])

        METRIC_LABELS = {
            "faithfulness": "Faithfulness",
            "answer_relevancy": "Answer Relevancy",
            "context_precision_with_reference": "Context Precision",
            "context_recall": "Context Recall",
            "answer_correctness": "Answer Correctness",
        }

        lines = [
            "# RAGAS Evaluation Report",
            "",
            f"**Generated**: {meta['timestamp']}",
            f"**Dataset**: {meta['dataset_path']} ({meta['num_samples']} samples, {meta['num_evaluated']} evaluated, {meta['num_errors']} errors)",
            f"**Judge Model**: {meta['judge_model']} @ {meta['judge_base_url']}",
            f"**Generation Model**: {meta['generation_model']}",
            f"**Embedding Model**: {meta['embedding_model']}",
            "",
            "## Aggregate Scores",
            "",
        ]

        # Aggregate table
        metric_keys = list(agg.keys())
        header = "| Metric | Mean | Median | Std | Min | Max | N |"
        sep = "|--------|------|--------|-----|-----|-----|---|"
        lines.append(header)
        lines.append(sep)
        for mk in metric_keys:
            a = agg[mk]
            label = METRIC_LABELS.get(mk, mk)
            lines.append(
                f"| {label} | {a['mean']:.4f} | {a['median']:.4f} | {a['std']:.4f} | {a['min']:.4f} | {a['max']:.4f} | {a['count']} |"
            )

        # By query type
        if by_type:
            lines.extend(["", "## By Query Type", ""])
            type_header = (
                "| Type | Count | "
                + " | ".join(METRIC_LABELS.get(mk, mk).split()[-1] for mk in metric_keys)
                + " |"
            )
            type_sep = (
                "|------|-------|"
                + "|".join("--------" for _ in metric_keys)
                + "|"
            )
            lines.append(type_header)
            lines.append(type_sep)
            for entry in by_type:
                parts = [entry["group"], str(entry["count"])]
                for mk in metric_keys:
                    parts.append(f"{entry.get(f'{mk}_mean', 0):.4f}")
                lines.append("| " + " | ".join(parts) + " |")

        # By difficulty
        if by_diff:
            lines.extend(["", "## By Difficulty", ""])
            diff_header = (
                "| Difficulty | Count | "
                + " | ".join(METRIC_LABELS.get(mk, mk).split()[-1] for mk in metric_keys)
                + " |"
            )
            diff_sep = (
                "|------------|-------|"
                + "|".join("--------" for _ in metric_keys)
                + "|"
            )
            lines.append(diff_header)
            lines.append(diff_sep)
            for entry in by_diff:
                parts = [entry["group"], str(entry["count"])]
                for mk in metric_keys:
                    parts.append(f"{entry.get(f'{mk}_mean', 0):.4f}")
                lines.append("| " + " | ".join(parts) + " |")

        # Per-sample details
        lines.extend(["", "## Per-Sample Details", ""])
        for s in samples:
            scores = s.get("scores", {})
            score_str = ", ".join(
                f"{METRIC_LABELS.get(k, k).split()[-1]}={v:.2f}"
                for k, v in scores.items()
                if not (isinstance(v, float) and v != v)
            ) if scores else "N/A"

            error_note = f" [ERROR: {s['error']}]" if s.get("error") else ""
            lines.append(
                f"### {s['id']} ({s.get('query_type', '?')} / {s.get('difficulty', '?')}){error_note}"
            )
            lines.append(f"- **Question**: {s['question']}")
            lines.append(f"- **Reference**: {s['reference'][:200]}...")
            lines.append(f"- **Response**: {(s.get('response') or '')[:200]}...")
            lines.append(f"- **Scores**: {score_str}")
            lines.append("")

        return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────


def parse_args():
    p = argparse.ArgumentParser(
        description="Ragas-based RAG quality evaluation for GraphMind"
    )
    p.add_argument("--dataset", default=DEFAULT_DATASET, help="Path to dataset JSON")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file prefix")
    p.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="Ollama model for judging")
    p.add_argument("--limit", type=int, default=0, help="Only evaluate first N samples")
    p.add_argument("--skip-generation", action="store_true", help="Reuse cached pipeline results")
    return p.parse_args()


async def main():
    args = parse_args()

    evaluator = RagasEvaluator(judge_model=args.judge_model)

    print("Loading dataset...")
    dataset = evaluator.load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} samples from {args.dataset}")

    t0 = time.time()
    results = await evaluator.evaluate(
        dataset,
        limit=args.limit,
        skip_generation=args.skip_generation,
    )
    elapsed = time.time() - t0
    print(f"\nEvaluation completed in {elapsed:.1f}s")

    evaluator.generate_report(results, args.output)

    # Quick summary
    agg = results["aggregate"]
    print("\n── Summary ──")
    for mk, a in agg.items():
        label = {
            "faithfulness": "Faithfulness     ",
            "answer_relevancy": "Answer Relevancy",
            "context_precision_with_reference": "Context Precision",
            "context_recall": "Context Recall   ",
            "answer_correctness": "Answer Correctness",
        }.get(mk, mk)
        print(f"  {label}:  mean={a['mean']:.4f}  median={a['median']:.4f}  (n={a['count']})")

    if results["errors"]:
        print(f"\n  {len(results['errors'])} errors encountered — see report for details.")


if __name__ == "__main__":
    asyncio.run(main())
