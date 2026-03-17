#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from typing import Any

from generate_site_content import DEFAULT_LLM_RETRIES
from generate_site_content import DEFAULT_LLM_RETRY_DELAY_SECONDS
from generate_site_content import DEFAULT_LLM_TIMEOUT
from generate_site_content import LLMClient
from generate_site_content import Topic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the OpenAI-compatible content drafting endpoint.")
    parser.add_argument("--endpoint", default=os.environ.get("LLMFIT_CONTENT_LLM_ENDPOINT"))
    parser.add_argument("--api-key", default=os.environ.get("LLMFIT_CONTENT_LLM_API_KEY"))
    parser.add_argument("--model", default=os.environ.get("LLMFIT_CONTENT_LLM_MODEL", "auto"))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("LLMFIT_CONTENT_LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT)))
    parser.add_argument("--retries", type=int, default=int(os.environ.get("LLMFIT_CONTENT_LLM_RETRIES", DEFAULT_LLM_RETRIES)))
    parser.add_argument(
        "--retry-delay-seconds",
        type=float,
        default=float(os.environ.get("LLMFIT_CONTENT_LLM_RETRY_DELAY_SECONDS", DEFAULT_LLM_RETRY_DELAY_SECONDS)),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.endpoint or not args.api_key:
        print("missing endpoint or api key")
        return 2

    client = LLMClient(
        args.endpoint,
        args.api_key,
        args.model,
        timeout=args.timeout,
        retries=args.retries,
        retry_delay_seconds=args.retry_delay_seconds,
    )
    topic = Topic(
        topic_id="healthcheck-runtime",
        slug="healthcheck-runtime",
        kind="runtime",
        title_hint_en="Healthcheck local AI runtime planning",
        title_hint_zh="健康检查：本地 AI 运行时规划",
        description_hint_en="A healthcheck payload for the content drafting endpoint.",
        description_hint_zh="用于内容起草端点的健康检查负载。",
        priority=1,
        metadata={
            "title_en": "Healthcheck local AI runtime planning",
            "title_zh": "健康检查：本地 AI 运行时规划",
            "lede_en": "A test prompt for the content drafting path.",
            "lede_zh": "用于内容起草路径的测试提示。",
        },
    )
    stats: dict[str, Any] = {
        "count": 4,
        "median_recommended_ram": 16,
        "upper_recommended_ram": 24,
        "median_vram": 8,
        "median_context": 8192,
        "top_architectures": [("llama", 2), ("qwen", 2)],
    }

    result = client.draft_article(topic, [], stats)
    print(f"endpoint: {client.endpoint}")
    print(f"attempts: {result.attempts}")
    print(f"mode: {result.mode}")
    if result.error:
        print(f"error: {result.error}")
    if result.payload:
        print("status: ok")
        return 0
    print("status: fallback")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
