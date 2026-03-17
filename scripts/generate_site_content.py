#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import datetime as dt
import html
import json
import os
import re
import statistics
import time
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape


DEFAULT_SITE_URL = "https://www.igeminicli.cn"
DEFAULT_STATE_FILE = "site/content-manifest.json"
DEFAULT_COUNT = 4
DEFAULT_LLM_TIMEOUT = 60
DEFAULT_LLM_RETRIES = 2
DEFAULT_LLM_RETRY_DELAY_SECONDS = 3.0

STATIC_ROUTES = [
    ("/", "/zh/"),
    ("/docs/", "/zh/docs/"),
    ("/use-cases/", "/zh/use-cases/"),
    ("/api/", "/zh/api/"),
    ("/self-host/", "/zh/self-host/"),
    ("/compare/", "/zh/compare/"),
    ("/faq/", "/zh/faq/"),
    ("/insights/", "/zh/insights/"),
    ("/insights/hardware/", "/zh/insights/hardware/"),
    ("/insights/families/", "/zh/insights/families/"),
    ("/insights/runtimes/", "/zh/insights/runtimes/"),
]

USE_CASES = [
    {
        "id": "coding",
        "label_en": "coding",
        "label_zh": "编程",
        "search_en": "coding models",
        "search_zh": "编程模型",
        "keywords": ["code", "coding", "completion", "math and code"],
        "intent_en": "developers choosing a model for code generation, refactoring, and repository work",
        "intent_zh": "希望做代码生成、重构和仓库辅助的开发者",
        "priority": 12,
    },
    {
        "id": "chat",
        "label_en": "chat",
        "label_zh": "对话",
        "search_en": "chat models",
        "search_zh": "对话模型",
        "keywords": ["instruction", "chat", "general purpose"],
        "intent_en": "general-purpose local assistants, internal copilots, and lightweight operator workflows",
        "intent_zh": "用于通用问答、本地助手和轻量运营场景的用户",
        "priority": 10,
    },
    {
        "id": "reasoning",
        "label_en": "reasoning",
        "label_zh": "推理",
        "search_en": "reasoning models",
        "search_zh": "推理模型",
        "keywords": ["reasoning", "chain-of-thought", "step-by-step", "math"],
        "intent_en": "teams optimizing for longer thinking tasks and more deliberate output quality",
        "intent_zh": "更关注复杂推理、长思考任务和更稳输出质量的团队",
        "priority": 11,
    },
    {
        "id": "multimodal",
        "label_en": "multimodal",
        "label_zh": "多模态",
        "search_en": "multimodal models",
        "search_zh": "多模态模型",
        "keywords": ["multimodal", "vision", "image"],
        "intent_en": "operators evaluating image-aware local assistants or inspection workflows",
        "intent_zh": "需要图像理解、本地视觉助手或质检类流程的团队",
        "priority": 9,
    },
    {
        "id": "lightweight",
        "label_en": "lightweight",
        "label_zh": "轻量",
        "search_en": "lightweight models",
        "search_zh": "轻量模型",
        "keywords": ["lightweight", "edge", "on-device", "rag", "embedding"],
        "intent_en": "edge deployments, small machines, and budget-conscious local AI experiments",
        "intent_zh": "面向边缘设备、小机器和预算敏感型本地 AI 场景",
        "priority": 8,
    },
]

HARDWARE_PROFILES = [
    {"id": "8g-cpu", "ram": 8, "vram": 0, "form_en": "8GB RAM CPU-only mini PC", "form_zh": "8GB 内存纯 CPU 小主机", "priority": 73},
    {"id": "16g-cpu", "ram": 16, "vram": 0, "form_en": "16GB RAM CPU-only laptop", "form_zh": "16GB 内存纯 CPU 笔记本", "priority": 81},
    {"id": "16g-8v", "ram": 16, "vram": 8, "form_en": "16GB RAM laptop with 8GB VRAM", "form_zh": "16GB 内存 + 8GB 显存笔记本", "priority": 91},
    {"id": "24g-8v", "ram": 24, "vram": 8, "form_en": "24GB RAM creator laptop with 8GB VRAM", "form_zh": "24GB 内存 + 8GB 显存创作者笔记本", "priority": 88},
    {"id": "24g-12v", "ram": 24, "vram": 12, "form_en": "24GB RAM desktop with 12GB VRAM", "form_zh": "24GB 内存 + 12GB 显存桌面机", "priority": 89},
    {"id": "32g-cpu", "ram": 32, "vram": 0, "form_en": "32GB RAM CPU-heavy workstation", "form_zh": "32GB 内存 CPU 工作站", "priority": 86},
    {"id": "32g-12v", "ram": 32, "vram": 12, "form_en": "32GB RAM desktop with 12GB VRAM", "form_zh": "32GB 内存 + 12GB 显存桌面机", "priority": 95},
    {"id": "32g-16v", "ram": 32, "vram": 16, "form_en": "32GB RAM desktop with 16GB VRAM", "form_zh": "32GB 内存 + 16GB 显存桌面机", "priority": 96},
    {"id": "48g-16v", "ram": 48, "vram": 16, "form_en": "48GB RAM workstation with 16GB VRAM", "form_zh": "48GB 内存 + 16GB 显存工作站", "priority": 90},
    {"id": "48g-24v", "ram": 48, "vram": 24, "form_en": "48GB RAM workstation with 24GB VRAM", "form_zh": "48GB 内存 + 24GB 显存工作站", "priority": 94},
    {"id": "64g-24v", "ram": 64, "vram": 24, "form_en": "64GB RAM local AI workstation with 24GB VRAM", "form_zh": "64GB 内存 + 24GB 显存本地 AI 工作站", "priority": 97},
    {"id": "64g-48v", "ram": 64, "vram": 48, "form_en": "64GB RAM GPU node with 48GB VRAM", "form_zh": "64GB 内存 + 48GB 显存 GPU 节点", "priority": 93},
    {"id": "96g-24v", "ram": 96, "vram": 24, "form_en": "96GB RAM shared team node with 24GB VRAM", "form_zh": "96GB 内存 + 24GB 显存团队共享节点", "priority": 87},
    {"id": "96g-48v", "ram": 96, "vram": 48, "form_en": "96GB RAM inference server with 48GB VRAM", "form_zh": "96GB 内存 + 48GB 显存推理服务器", "priority": 92},
]

FAMILY_TARGETS = [
    "Qwen3",
    "Qwen2.5",
    "Llama",
    "DeepSeek",
    "Phi",
    "gemma",
    "Mistral",
    "GLM",
    "SmolLM",
    "OLMo",
]

RUNTIME_TOPICS = [
    {
        "id": "runtime-ollama-laptops",
        "slug": "ollama-model-selection-for-laptops",
        "title_en": "Ollama model selection for laptops: how to stay realistic about RAM and VRAM",
        "title_zh": "面向笔记本的 Ollama 选型指南：如何更现实地看待内存和显存",
        "description_en": "A practical guide to choosing Ollama-compatible local models without overcommitting weak laptop hardware.",
        "description_zh": "帮助用户在笔记本上为 Ollama 选择更现实的本地模型，而不是盲目追大参数量。",
        "lede_en": "Ollama makes pulling a model easy. The hard part is deciding which model is worth pulling onto a laptop in the first place.",
        "lede_zh": "Ollama 让拉模型变得很简单，真正困难的是先判断笔记本到底适合拉哪一类模型。",
        "priority": 84,
    },
    {
        "id": "runtime-mlx-apple-silicon",
        "slug": "mlx-for-apple-silicon-local-ai-planning",
        "title_en": "MLX for Apple Silicon: planning local AI around unified memory instead of GPU myths",
        "title_zh": "MLX 与 Apple Silicon：围绕统一内存规划本地 AI，而不是迷信显卡参数",
        "description_en": "Use unified-memory-aware planning to choose better MLX model paths on Apple Silicon.",
        "description_zh": "帮助 Apple Silicon 用户围绕统一内存做 MLX 选型与部署规划。",
        "lede_en": "Apple Silicon changes the local AI conversation because memory, bandwidth, and model format interact differently than on a classic desktop GPU box.",
        "lede_zh": "Apple Silicon 会改变本地 AI 的判断方式，因为它的内存、带宽和模型格式关系和传统 GPU 主机并不一样。",
        "priority": 83,
    },
    {
        "id": "runtime-llamacpp-cpu",
        "slug": "llamacpp-on-cpu-only-machines",
        "title_en": "llama.cpp on CPU-only machines: where it still makes sense",
        "title_zh": "纯 CPU 机器使用 llama.cpp：它在哪些场景下依然值得",
        "description_en": "Understand when CPU-only local AI is still practical and where fit analysis matters most.",
        "description_zh": "帮助用户理解纯 CPU 本地 AI 仍然有价值的场景，以及为什么更需要适配分析。",
        "lede_en": "CPU-only local AI is not dead. It just punishes unrealistic model choice much faster than a strong GPU workstation does.",
        "lede_zh": "纯 CPU 本地 AI 不是不能做，只是它会更快惩罚不现实的模型选择。",
        "priority": 82,
    },
]

KIND_META = {
    "hardware": {
        "slug": "hardware",
        "label_en": "Hardware fit",
        "label_zh": "硬件适配",
        "title_en": "Hardware fit guides for realistic local AI deployments",
        "title_zh": "面向真实本地 AI 部署的硬件适配指南",
        "description_en": "Pages focused on RAM, VRAM, and machine-class planning before you commit to a local model download.",
        "description_zh": "围绕内存、显存和机器级规划展开的页面，帮助用户在下载本地模型前先做现实判断。",
        "intro_en": "Use these pages to narrow local AI decisions by machine budget, not by hype. The goal is to identify what is likely to fit before runtime friction shows up in production work.",
        "intro_zh": "这些页面用于按机器预算而不是按热度缩小本地 AI 决策范围。重点是在运行时问题真正影响生产工作前，先判断什么更可能适配。",
    },
    "family": {
        "slug": "families",
        "label_en": "Model families",
        "label_zh": "模型家族",
        "title_en": "Model family deployment guides for local AI teams",
        "title_zh": "面向本地 AI 团队的模型家族部署指南",
        "description_en": "Family-level pages that turn broad interest in Llama, Qwen, DeepSeek, and similar lines into concrete fit decisions.",
        "description_zh": "把用户对 Llama、Qwen、DeepSeek 等家族的广泛兴趣，转化为具体适配决策的专题页面。",
        "intro_en": "Search traffic often starts with a family name. These guides convert that demand into practical decisions about memory, context, runtime support, and deployment scope.",
        "intro_zh": "搜索流量通常从家族名开始。这些指南会把这种需求转化为关于内存、上下文、运行时支持和部署范围的实际判断。",
    },
    "runtime": {
        "slug": "runtimes",
        "label_en": "Runtime planning",
        "label_zh": "运行时规划",
        "title_en": "Runtime planning pages for Ollama, MLX, and llama.cpp workflows",
        "title_zh": "面向 Ollama、MLX 和 llama.cpp 工作流的运行时规划页面",
        "description_en": "Runtime-specific content that explains where operational convenience ends and hardware fit decisions still matter.",
        "description_zh": "围绕运行时的内容，说明操作便利性在哪一步结束，以及为什么硬件适配判断依然重要。",
        "intro_en": "Runtime tools reduce operational friction, but they do not rescue an unrealistic placement decision. Use these pages to choose a runtime path that matches the machine and workload.",
        "intro_zh": "运行时工具可以降低操作门槛，但它们无法挽救不现实的放置决策。用这些页面选择更匹配机器和工作负载的运行时路径。",
    },
}

EN_PAGE_LABELS = {
    "home": "Home",
    "docs": "Docs",
    "use_cases": "Use Cases",
    "api": "API",
    "self_host": "Self-Host",
    "faq": "FAQ",
    "insights": "Insights",
    "github": "GitHub",
    "menu": "Menu",
}

ZH_PAGE_LABELS = {
    "home": "首页",
    "docs": "文档",
    "use_cases": "应用场景",
    "api": "API",
    "self_host": "自托管",
    "faq": "常见问题",
    "insights": "洞察",
    "github": "GitHub",
    "menu": "菜单",
}


@dataclass
class Topic:
    topic_id: str
    slug: str
    kind: str
    title_hint_en: str
    title_hint_zh: str
    description_hint_en: str
    description_hint_zh: str
    priority: int
    metadata: dict[str, Any]


@dataclass
class DraftResult:
    payload: dict[str, Any] | None
    mode: str
    attempts: int
    error: str | None


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def human_number(num: float | int | None) -> str:
    if num is None:
        return "unknown"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(int(num))


def home_path(locale: str) -> str:
    return "/" if locale == "en" else "/zh/"


def article_path(article: dict[str, Any], locale: str) -> str:
    prefix = "/insights/" if locale == "en" else "/zh/insights/"
    return f"{prefix}{article['slug']}/"


def kind_index_path(kind: str, locale: str) -> str:
    prefix = "/insights/" if locale == "en" else "/zh/insights/"
    return f"{prefix}{KIND_META[kind]['slug']}/"


def feed_path(locale: str) -> str:
    return "/feed.xml" if locale == "en" else "/zh/feed.xml"


def kind_label(kind: str, locale: str) -> str:
    key = "label_en" if locale == "en" else "label_zh"
    return str(KIND_META[kind][key])


def topic_tokens(article: dict[str, Any]) -> set[str]:
    topic_id = str(article.get("topic_id", ""))
    tokens = {token for token in re.split(r"[^a-z0-9]+", topic_id.lower()) if token}
    return tokens - {"hardware", "family", "runtime", "local", "guide", "deployment"}


def select_related_articles(article: dict[str, Any], articles: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    def score(candidate: dict[str, Any]) -> tuple[int, str, str]:
        if candidate["slug"] == article["slug"]:
            return (-1, "", "")
        relatedness = 0
        if candidate.get("kind") == article.get("kind"):
            relatedness += 6
        shared_tokens = topic_tokens(article) & topic_tokens(candidate)
        relatedness += len(shared_tokens) * 3
        if candidate.get("label_en") == article.get("label_en"):
            relatedness += 2
        if candidate.get("published_on") == article.get("published_on"):
            relatedness += 1
        return (relatedness, str(candidate.get("published_on", "")), candidate["slug"])

    ranked = sorted(articles, key=score, reverse=True)
    selected: list[dict[str, Any]] = []

    for candidate in ranked:
        if candidate["slug"] == article["slug"]:
            continue
        if score(candidate)[0] <= 0:
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            return selected

    for candidate in ranked:
        if candidate["slug"] == article["slug"] or candidate in selected:
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            break

    return selected


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def load_catalog(repo_root: Path) -> list[dict[str, Any]]:
    catalog_path = repo_root / "llmfit-core" / "data" / "hf_models.json"
    with catalog_path.open() as handle:
        return json.load(handle)


def infer_family(name: str) -> str:
    model_part = name.split("/", 1)[-1]
    match = re.match(r"([A-Za-z][A-Za-z0-9.+]+)", model_part)
    if not match:
        return model_part
    token = match.group(1)
    return token.rstrip(".")


def use_case_matches(entry: dict[str, Any], use_case: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(entry.get("use_case", "")),
            str(entry.get("pipeline_tag", "")),
            str(entry.get("architecture", "")),
            str(entry.get("name", "")),
        ]
    ).lower()
    return any(keyword in haystack for keyword in use_case["keywords"])


def filter_hardware_entries(
    catalog: list[dict[str, Any]],
    ram: int,
    vram: int,
    use_case: dict[str, Any],
) -> list[dict[str, Any]]:
    results = []
    vram_limit = max(0.5, float(vram) + 0.5)
    for entry in catalog:
        recommended_ram = float(entry.get("recommended_ram_gb") or entry.get("min_ram_gb") or 0.0)
        min_vram = float(entry.get("min_vram_gb") or 0.0)
        if recommended_ram > ram:
            continue
        if min_vram > vram_limit:
            continue
        if not use_case_matches(entry, use_case):
            continue
        results.append(entry)
    return sorted(
        results,
        key=lambda item: (
            float(item.get("hf_downloads") or 0),
            float(item.get("context_length") or 0),
            float(item.get("parameters_raw") or 0),
        ),
        reverse=True,
    )


def build_hardware_topics(catalog: list[dict[str, Any]]) -> list[Topic]:
    topics: list[Topic] = []
    for profile in HARDWARE_PROFILES:
        for use_case in USE_CASES:
            if use_case["id"] == "multimodal" and profile["vram"] == 0:
                continue
            results = filter_hardware_entries(catalog, profile["ram"], profile["vram"], use_case)
            if len(results) < 4:
                continue
            slug = slugify(
                f"{use_case['id']}-models-for-{profile['ram']}gb-ram"
                + (f"-and-{profile['vram']}gb-vram" if profile["vram"] else "-cpu-only")
            )
            title_en = (
                f"Best local AI {use_case['search_en']} for {profile['ram']}GB RAM"
                + (f" and {profile['vram']}GB VRAM" if profile["vram"] else " on CPU-only machines")
            )
            title_zh = (
                f"{profile['ram']}GB 内存"
                + (f" + {profile['vram']}GB 显存" if profile["vram"] else "纯 CPU")
                + f" 适合跑哪些本地 {use_case['search_zh']}？"
            )
            description_en = (
                f"Use bundled LLMFit catalog data to shortlist realistic {use_case['search_en']} for a "
                f"{profile['form_en']} without downloading models that are too large."
            )
            description_zh = (
                f"基于 LLMFit 内置目录数据，为 {profile['form_zh']} 筛选更现实的 {use_case['search_zh']}，"
                "避免先下载再发现模型过重。"
            )
            topics.append(
                Topic(
                    topic_id=f"hardware-{profile['id']}-{use_case['id']}",
                    slug=slug,
                    kind="hardware",
                    title_hint_en=title_en,
                    title_hint_zh=title_zh,
                    description_hint_en=description_en,
                    description_hint_zh=description_zh,
                    priority=profile["priority"] + use_case["priority"],
                    metadata={"profile": profile, "use_case": use_case},
                )
            )
    return topics


def family_entries(catalog: list[dict[str, Any]], family_name: str) -> list[dict[str, Any]]:
    needle = family_name.lower()
    matches = [entry for entry in catalog if needle in str(entry.get("name", "")).lower()]
    return sorted(matches, key=lambda item: float(item.get("hf_downloads") or 0), reverse=True)


def build_family_topics(catalog: list[dict[str, Any]]) -> list[Topic]:
    topics: list[Topic] = []
    for family_name in FAMILY_TARGETS:
        matches = family_entries(catalog, family_name)
        if len(matches) < 3:
            continue
        title_en = f"{family_name} local deployment guide: what hardware usually fits"
        title_zh = f"{family_name} 本地部署指南：通常需要怎样的硬件"
        topics.append(
            Topic(
                topic_id=f"family-{slugify(family_name)}",
                slug=slugify(f"{family_name}-local-deployment-guide"),
                kind="family",
                title_hint_en=title_en,
                title_hint_zh=title_zh,
                description_hint_en=(
                    f"An original LLMFit guide to understanding how {family_name} models usually map to local hardware and deployment decisions."
                ),
                description_hint_zh=(
                    f"帮助用户理解 {family_name} 系列模型通常如何映射到本地硬件与部署决策。"
                ),
                priority=80 + min(len(matches), 15),
                metadata={"family_name": family_name},
            )
        )
    return topics


def build_runtime_topics() -> list[Topic]:
    topics: list[Topic] = []
    for item in RUNTIME_TOPICS:
        topics.append(
            Topic(
                topic_id=item["id"],
                slug=item["slug"],
                kind="runtime",
                title_hint_en=item["title_en"],
                title_hint_zh=item["title_zh"],
                description_hint_en=item["description_en"],
                description_hint_zh=item["description_zh"],
                priority=item["priority"],
                metadata=item,
            )
        )
    return topics


def build_topic_pool(catalog: list[dict[str, Any]]) -> list[Topic]:
    pool = build_hardware_topics(catalog) + build_family_topics(catalog) + build_runtime_topics()
    return sorted(pool, key=lambda topic: (-topic.priority, topic.slug))


def summarize_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    recommended_ram_values = [float(entry.get("recommended_ram_gb") or entry.get("min_ram_gb") or 0) for entry in entries]
    vram_values = [float(entry.get("min_vram_gb") or 0) for entry in entries]
    context_values = [float(entry.get("context_length") or 0) for entry in entries if entry.get("context_length")]
    architectures = Counter(entry.get("architecture") or "unknown" for entry in entries)
    return {
        "count": len(entries),
        "median_recommended_ram": statistics.median(recommended_ram_values) if recommended_ram_values else 0,
        "upper_recommended_ram": quantile(recommended_ram_values, 0.75) if recommended_ram_values else 0,
        "median_vram": statistics.median(vram_values) if vram_values else 0,
        "median_context": statistics.median(context_values) if context_values else 0,
        "top_architectures": architectures.most_common(3),
    }


def pick_examples(entries: list[dict[str, Any]], count: int = 5) -> list[dict[str, Any]]:
    selected = []
    seen = set()
    for entry in entries:
        family = infer_family(str(entry.get("name", ""))).lower()
        if family in seen:
            continue
        seen.add(family)
        selected.append(entry)
        if len(selected) >= count:
            break
    if len(selected) < count:
        for entry in entries:
            if entry not in selected:
                selected.append(entry)
                if len(selected) >= count:
                    break
    return selected


def normalize_llm_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip().rstrip("/")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    if endpoint.endswith("/v1"):
        return f"{endpoint}/chat/completions"
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.path.endswith("/v1"):
        return f"{endpoint}/chat/completions"
    return f"{endpoint}/v1/chat/completions"


def message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part.strip())
    return ""


def extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def clean_llm_section(section: Any) -> dict[str, Any]:
    if not isinstance(section, dict):
        return {}

    cleaned: dict[str, Any] = {}
    lede = section.get("lede")
    takeaway = section.get("takeaway")
    why_items = section.get("why_it_matters")
    faq_items = section.get("faq")

    if isinstance(lede, str) and lede.strip():
        cleaned["lede"] = lede.strip()
    if isinstance(takeaway, str) and takeaway.strip():
        cleaned["takeaway"] = takeaway.strip()
    if isinstance(why_items, list):
        why_clean = [str(item).strip() for item in why_items[:3] if str(item).strip()]
        if why_clean:
            cleaned["why_it_matters"] = why_clean
    if isinstance(faq_items, list):
        faq_clean = []
        for item in faq_items[:3]:
            if not isinstance(item, dict):
                continue
            question = str(item.get("q", "")).strip()
            answer = str(item.get("a", "")).strip()
            if question and answer:
                faq_clean.append({"q": question, "a": answer})
        if faq_clean:
            cleaned["faq"] = faq_clean
    return cleaned


def validate_llm_payload(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(payload, dict):
        return None, "top-level response was not a JSON object"

    cleaned: dict[str, Any] = {}
    useful_sections = 0
    for locale in ("en", "zh"):
        section = clean_llm_section(payload.get(locale))
        cleaned[locale] = section
        if section:
            useful_sections += 1

    if useful_sections == 0:
        return None, "response did not include usable bilingual editorial fields"
    return cleaned, None


class LLMClient:
    def __init__(self, endpoint: str, api_key: str, model: str, timeout: int = DEFAULT_LLM_TIMEOUT, retries: int = DEFAULT_LLM_RETRIES, retry_delay_seconds: float = DEFAULT_LLM_RETRY_DELAY_SECONDS):
        self.endpoint = normalize_llm_endpoint(endpoint)
        self.api_key = api_key
        self.model = model
        self.timeout = max(5, int(timeout))
        self.retries = max(0, int(retries))
        self.retry_delay_seconds = max(0.0, float(retry_delay_seconds))

    def _request_json_payload(self, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode()
            except UnicodeDecodeError:
                detail = "unreadable error body"
            return None, f"http {exc.code}: {detail[:240]}"
        except urllib.error.URLError as exc:
            return None, f"url error: {exc.reason}"
        except TimeoutError:
            return None, "request timed out"
        except json.JSONDecodeError:
            return None, "endpoint returned invalid JSON"

        if isinstance(response_body, dict) and response_body.get("error"):
            return None, f"api error: {response_body['error']}"
        return response_body, None

    def draft_article(self, topic: Topic, examples: list[dict[str, Any]], stats: dict[str, Any]) -> DraftResult:
        system_prompt = textwrap.dedent(
            """
            You are an editorial engine for an open-source local AI infrastructure project.
            Write original bilingual content for search traffic without spammy tactics.
            Hard rules:
            - Focus on local AI model selection, hardware fit, deployment planning, and runtime choices.
            - Do not copy documentation or marketing copy from other sites.
            - Do not fabricate benchmark wins, release news, endorsements, or real-time claims.
            - Do not include legal, medical, financial, political, adult, gambling, or deceptive content.
            - Stay practical, technical, and helpful.
            - Return strict JSON only.
            """
        ).strip()

        example_rows = [
            {
                "name": entry.get("name"),
                "architecture": entry.get("architecture"),
                "use_case": entry.get("use_case"),
                "recommended_ram_gb": entry.get("recommended_ram_gb"),
                "min_vram_gb": entry.get("min_vram_gb"),
                "context_length": entry.get("context_length"),
                "hf_downloads": entry.get("hf_downloads"),
            }
            for entry in examples[:5]
        ]

        user_prompt = {
            "topic": {
                "kind": topic.kind,
                "title_hint_en": topic.title_hint_en,
                "title_hint_zh": topic.title_hint_zh,
                "description_hint_en": topic.description_hint_en,
                "description_hint_zh": topic.description_hint_zh,
                "metadata": topic.metadata,
            },
            "catalog_summary": stats,
            "examples": example_rows,
            "return_schema": {
                "en": {
                    "lede": "2-3 sentence introduction",
                    "why_it_matters": ["three short bullets"],
                    "takeaway": "one short paragraph",
                    "faq": [{"q": "question", "a": "answer"}, {"q": "question", "a": "answer"}, {"q": "question", "a": "answer"}],
                },
                "zh": {
                    "lede": "2-3 sentence introduction in Simplified Chinese",
                    "why_it_matters": ["three short bullets in Simplified Chinese"],
                    "takeaway": "one short paragraph in Simplified Chinese",
                    "faq": [{"q": "question", "a": "answer"}, {"q": "question", "a": "answer"}, {"q": "question", "a": "answer"}],
                },
            },
        }

        payload = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ],
        }

        last_error: str | None = None
        total_attempts = self.retries + 1

        for attempt in range(1, total_attempts + 1):
            response_body, request_error = self._request_json_payload(payload)
            if request_error:
                last_error = request_error
            else:
                try:
                    content = response_body["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    last_error = "response body did not contain choices[0].message.content"
                else:
                    content_text = message_content_to_text(content)
                    if not content_text.strip():
                        last_error = "message content was empty"
                    else:
                        extracted = extract_json_object(content_text)
                        if not extracted:
                            last_error = "message content did not contain a parseable JSON object"
                        else:
                            cleaned_payload, validation_error = validate_llm_payload(extracted)
                            if cleaned_payload:
                                return DraftResult(payload=cleaned_payload, mode="llm", attempts=attempt, error=None)
                            last_error = validation_error

            if attempt < total_attempts:
                print(f"[content-llm] attempt {attempt}/{total_attempts} failed for {topic.slug}: {last_error}; retrying")
                time.sleep(self.retry_delay_seconds * attempt)

        return DraftResult(payload=None, mode="fallback", attempts=total_attempts, error=last_error or "unknown llm error")


def fallback_copy(topic: Topic, stats: dict[str, Any]) -> dict[str, Any]:
    if topic.kind == "hardware":
        profile = topic.metadata["profile"]
        use_case = topic.metadata["use_case"]
        lede_en = (
            f"{profile['form_en']} users usually waste time in the same place: they download a model that looks attractive on paper "
            f"and only then discover the memory, context, or runtime trade-off is wrong for {use_case['label_en']} work. "
            "This page uses the bundled LLMFit catalog as a planning layer before that mistake happens."
        )
        lede_zh = (
            f"{profile['form_zh']} 用户最常见的浪费，往往不是推理本身，而是先下载一个看起来很强的模型，"
            f"然后才发现它并不适合当前机器上的 {use_case['label_zh']} 场景。"
            "这篇页面就是用 LLMFit 的内置目录，提前把这种错误过滤掉。"
        )
        why_en = [
            f"Shortlists models that usually stay inside a {profile['ram']}GB RAM budget"
            + (f" with roughly {profile['vram']}GB VRAM available" if profile["vram"] else " on CPU-only systems"),
            f"Biases the discussion toward {use_case['search_en']} instead of generic model hype",
            "Turns hardware fit into an operational starting point you can validate with the CLI or API",
        ]
        why_zh = [
            f"先把结果限制在 {profile['ram']}GB 内存"
            + (f" 和约 {profile['vram']}GB 显存可承受的范围内" if profile["vram"] else " 的纯 CPU 范围内"),
            f"重点讨论 {use_case['search_zh']}，而不是泛化的模型宣传",
            "把选型问题先收敛成可执行的起点，再交给 CLI 或 API 验证",
        ]
        takeaway_en = (
            f"The useful question is not whether a model can start at all, but whether it leaves enough headroom for {use_case['label_en']} "
            "to feel stable in a real workflow. Treat this page as a first shortlist, then verify the exact node with `llmfit recommend`."
        )
        takeaway_zh = (
            f"真正有用的问题不是模型能不能勉强启动，而是它在 {use_case['label_zh']} 工作流里是否还能留下足够余量。"
            "这类页面应该被当作第一轮 shortlist，然后再用 `llmfit recommend` 对真实节点做最终确认。"
        )
    elif topic.kind == "family":
        family_name = topic.metadata["family_name"]
        lede_en = (
            f"{family_name} is not one model, one memory footprint, or one deployment story. "
            "Family-level search intent is useful, but only if it leads to a better hardware decision instead of a vague brand preference."
        )
        lede_zh = (
            f"{family_name} 不是单一模型，也不是单一内存占用，更不是单一路线。"
            "围绕家族名搜索是有价值的，但前提是它最终能导向更准确的硬件决策，而不是停留在品牌偏好。"
        )
        why_en = [
            f"Shows how {family_name} spans small, medium, and heavier local deployment paths",
            "Connects family-level interest to RAM, VRAM, and context constraints",
            "Keeps the discussion grounded in shipped catalog data rather than headline-level hype",
        ]
        why_zh = [
            f"解释 {family_name} 在轻量、中型和更重本地部署路线上的跨度",
            "把家族级兴趣点和内存、显存、上下文限制真正连接起来",
            "让讨论回到已收录目录数据，而不是停留在标题党式的热度上",
        ]
        takeaway_en = (
            f"The safest way to approach {family_name} locally is to think in fit ranges, not one magic model name. "
            "Use the family to narrow intent, then let the actual machine decide the final candidate."
        )
        takeaway_zh = (
            f"本地使用 {family_name} 更稳妥的方式，是先理解它的适配区间，而不是寻找一个所谓万能型号。"
            "先用家族名缩小方向，再让真实机器决定最终候选。"
        )
    else:
        lede_en = topic.metadata["lede_en"]
        lede_zh = topic.metadata["lede_zh"]
        why_en = [
            "Clarifies where runtime convenience ends and hardware fit analysis begins",
            "Helps avoid overcommitting local hardware before a workflow is proven",
            "Pairs product messaging with operational checks you can run today",
        ]
        why_zh = [
            "说明运行时便利性和硬件适配分析之间的边界",
            "帮助用户在工作流验证前避免对本地硬件过度承诺",
            "把产品表达和今天就能执行的运营检查结合起来",
        ]
        takeaway_en = (
            "Convenience layers matter, but they work best when the placement decision is already realistic. "
            "Use LLMFit as the decision layer before the runtime or container workflow begins."
        )
        takeaway_zh = (
            "运行时层当然重要，但前提是前面的放置决策已经足够现实。"
            "更稳妥的做法，是先用 LLMFit 做决策层，再进入运行时或容器层。"
        )

    return {
        "en": {
            "lede": lede_en,
            "why_it_matters": why_en,
            "takeaway": takeaway_en,
            "faq": fallback_faq(topic, stats, "en"),
        },
        "zh": {
            "lede": lede_zh,
            "why_it_matters": why_zh,
            "takeaway": takeaway_zh,
            "faq": fallback_faq(topic, stats, "zh"),
        },
    }


def fallback_faq(topic: Topic, stats: dict[str, Any], locale: str) -> list[dict[str, str]]:
    count = stats.get("count", 0)
    median_context = int(stats.get("median_context") or 0)
    if locale == "en":
        return [
            {
                "q": "Is this page the final deployment answer?",
                "a": "No. It is a planning shortcut built from the bundled LLMFit catalog. You should still validate the exact node with the CLI or REST API.",
            },
            {
                "q": "Why focus on fit instead of a benchmark chart?",
                "a": f"Because this topic still has {count} candidate catalog entries after hardware filtering. Real deployments fail on memory and runtime limits before leaderboard differences matter.",
            },
            {
                "q": "What should I verify next?",
                "a": (
                    "Check detected hardware, shortlist a few candidates, and confirm context requirements."
                    + (f" The median context in this slice is about {median_context}." if median_context else "")
                ),
            },
        ]
    return [
        {
            "q": "这篇页面能直接替代最终部署结论吗？",
            "a": "不能。它只是基于 LLMFit 内置目录做出的规划起点，最终仍应通过 CLI 或 REST API 在真实节点上验证。",
        },
        {
            "q": "为什么不直接看 Benchmark 榜单？",
            "a": f"因为在完成硬件过滤后，这个主题下仍然有 {count} 个候选条目。现实部署往往先败给内存和运行时限制，而不是榜单差异。",
        },
        {
            "q": "接下来应该验证什么？",
            "a": "先确认真实硬件检测结果，再筛选少量候选，并核对上下文需求。"
            + (f" 这一批候选的上下文中位数大约是 {median_context}。" if median_context else ""),
        },
    ]


def merge_copy(topic: Topic, stats: dict[str, Any], llm_payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = fallback_copy(topic, stats)
    if not llm_payload:
        return payload

    for locale in ("en", "zh"):
        section = llm_payload.get(locale) or {}
        if isinstance(section.get("lede"), str) and section["lede"].strip():
            payload[locale]["lede"] = section["lede"].strip()
        if isinstance(section.get("why_it_matters"), list) and section["why_it_matters"]:
            payload[locale]["why_it_matters"] = [str(item).strip() for item in section["why_it_matters"][:3] if str(item).strip()]
        if isinstance(section.get("takeaway"), str) and section["takeaway"].strip():
            payload[locale]["takeaway"] = section["takeaway"].strip()
        if isinstance(section.get("faq"), list) and section["faq"]:
            cleaned = []
            for item in section["faq"][:3]:
                if not isinstance(item, dict):
                    continue
                question = str(item.get("q", "")).strip()
                answer = str(item.get("a", "")).strip()
                if question and answer:
                    cleaned.append({"q": question, "a": answer})
            if cleaned:
                payload[locale]["faq"] = cleaned
    return payload


def example_card(entry: dict[str, Any], locale: str) -> str:
    label_context = "Context" if locale == "en" else "上下文"
    label_ram = "Recommended RAM" if locale == "en" else "建议内存"
    label_vram = "Min VRAM" if locale == "en" else "最低显存"
    label_downloads = "Downloads" if locale == "en" else "下载量"
    return f"""
        <article class="content-card">
          <h3>{html.escape(str(entry.get("name", "Unknown model")))}</h3>
          <p>{html.escape(str(entry.get("use_case", "General purpose text generation")))}</p>
          <ul class="checklist">
            <li>{label_ram}: {html.escape(str(entry.get("recommended_ram_gb", "n/a")))}GB</li>
            <li>{label_vram}: {html.escape(str(entry.get("min_vram_gb", "n/a")))}GB</li>
            <li>{label_context}: {html.escape(str(entry.get("context_length", "n/a")))}</li>
            <li>{label_downloads}: {html.escape(human_number(float(entry.get("hf_downloads") or 0)))}</li>
          </ul>
        </article>
    """


def article_link_card(article: dict[str, Any], locale: str) -> str:
    is_en = locale == "en"
    title_text = article["title_en"] if is_en else article["title_zh"]
    description_text = article["description_en"] if is_en else article["description_zh"]
    article_date = article["published_on"]
    label = article["label_en"] if is_en else article["label_zh"]
    return f"""
        <a class="link-card insight-card" href="{article_path(article, locale)}">
          <div class="card-meta">
            <span class="section-pill">{html.escape(kind_label(article['kind'], locale))}</span>
            <em>{html.escape(article_date)}</em>
          </div>
          <strong>{html.escape(title_text)}</strong>
          <span>{html.escape(description_text)}</span>
          <p class="card-caption">{html.escape(label)}</p>
        </a>
    """


def kind_card(kind: str, locale: str, articles: list[dict[str, Any]]) -> str:
    is_en = locale == "en"
    meta = KIND_META[kind]
    key_title = "title_en" if is_en else "title_zh"
    key_description = "description_en" if is_en else "description_zh"
    matching = [article for article in articles if article.get("kind") == kind]
    count_label = f"{len(matching)} pages" if is_en else f"{len(matching)} 个页面"
    latest = matching[0]["published_on"] if matching else ("Not published yet" if is_en else "暂未发布")
    latest_label = "Latest update" if is_en else "最近更新"
    return f"""
        <a class="link-card category-card" href="{kind_index_path(kind, locale)}">
          <div class="card-meta">
            <span class="section-pill">{html.escape(kind_label(kind, locale))}</span>
            <em>{html.escape(count_label)}</em>
          </div>
          <strong>{html.escape(str(meta[key_title]))}</strong>
          <span>{html.escape(str(meta[key_description]))}</span>
          <p class="card-caption">{latest_label}: {html.escape(latest)}</p>
        </a>
    """


def build_article_data(topic: Topic, catalog: list[dict[str, Any]], llm_client: LLMClient | None) -> dict[str, Any]:
    if topic.kind == "hardware":
        profile = topic.metadata["profile"]
        use_case = topic.metadata["use_case"]
        entries = filter_hardware_entries(catalog, profile["ram"], profile["vram"], use_case)
        command = f"llmfit recommend --json --use-case {use_case['id']} --limit 5"
        label_en = f"{profile['ram']}GB RAM" + (f" / {profile['vram']}GB VRAM" if profile["vram"] else " / CPU-only")
        label_zh = f"{profile['ram']}GB 内存" + (f" / {profile['vram']}GB 显存" if profile["vram"] else " / 纯 CPU")
    elif topic.kind == "family":
        family_name = topic.metadata["family_name"]
        entries = family_entries(catalog, family_name)
        command = f'llmfit recommend --json --search "{family_name}" --limit 5'
        label_en = family_name
        label_zh = family_name
    else:
        entries = sorted(catalog, key=lambda item: float(item.get("hf_downloads") or 0), reverse=True)[:18]
        command = "llmfit system\nllmfit recommend --json --limit 5"
        label_en = topic.metadata["title_en"]
        label_zh = topic.metadata["title_zh"]

    stats = summarize_entries(entries)
    examples = pick_examples(entries, 5)
    draft_result = llm_client.draft_article(topic, examples, stats) if llm_client else DraftResult(payload=None, mode="fallback", attempts=0, error="llm not configured")
    copy_payload = merge_copy(topic, stats, draft_result.payload)
    draft_mode = draft_result.mode if draft_result.payload else "fallback"

    if topic.kind == "hardware":
        profile = topic.metadata["profile"]
        use_case = topic.metadata["use_case"]
        sections = {
            "en": [
                {
                    "heading": "What this hardware profile usually means",
                    "body": (
                        f"A {profile['form_en']} can support a serious local workflow when the model family, context budget, and runtime are chosen conservatively. "
                        f"In the bundled catalog slice for {use_case['search_en']}, this topic still leaves {stats['count']} viable entries after applying memory filters."
                    ),
                },
                {
                    "heading": "How to think about fit",
                    "body": (
                        f"The median recommended RAM in this slice is {stats['median_recommended_ram']:.1f}GB, and the upper quartile is about "
                        f"{stats['upper_recommended_ram']:.1f}GB. That is a useful reminder that 'technically runs' and 'comfortable daily use' are different thresholds."
                    ),
                },
                {
                    "heading": "What to verify with LLMFit",
                    "body": (
                        "Run the machine-local recommendation flow, confirm the detected runtime, and compare a small number of realistic models before you download anything heavyweight."
                    ),
                },
            ],
            "zh": [
                {
                    "heading": "这类硬件通常意味着什么",
                    "body": (
                        f"{profile['form_zh']} 并不等于只能做演示。只要模型家族、上下文预算和运行时选得保守，它依然可以支撑有实际价值的本地工作流。"
                        f"在面向 {use_case['search_zh']} 的目录切片中，经过内存过滤后仍有 {stats['count']} 个可用条目。"
                    ),
                },
                {
                    "heading": "应该如何理解适配度",
                    "body": (
                        f"这一批候选的建议内存中位数约为 {stats['median_recommended_ram']:.1f}GB，上四分位约为 {stats['upper_recommended_ram']:.1f}GB。"
                        "这提醒我们，“勉强能跑”和“适合日常使用”并不是同一个阈值。"
                    ),
                },
                {
                    "heading": "用 LLMFit 还要再确认什么",
                    "body": "先在真实机器上跑本地推荐流程，确认运行时和检测结果，再从少量现实候选中做最后决定，不要一开始就下载重量级模型。",
                },
            ],
        }
        metrics = {
            "en": [
                {"value": str(stats["count"]), "label": "catalog entries still viable after fit filtering"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "median recommended RAM in this slice"},
                {"value": f"{stats['median_context']:.0f}", "label": "median context length across the filtered set"},
            ],
            "zh": [
                {"value": str(stats["count"]), "label": "内存过滤后仍可用的目录条目数"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "当前切片的建议内存中位数"},
                {"value": f"{stats['median_context']:.0f}", "label": "当前候选集合的上下文中位数"},
            ],
        }
    elif topic.kind == "family":
        family_name = topic.metadata["family_name"]
        top_architectures = ", ".join(name for name, _ in stats["top_architectures"]) or "mixed architectures"
        sections = {
            "en": [
                {
                    "heading": f"Why {family_name} search traffic needs a fit layer",
                    "body": (
                        f"Search interest in {family_name} usually starts with a family name, but deployment success depends on memory, quantization, context length, and runtime support. "
                        "This page reframes the family as a placement question."
                    ),
                },
                {
                    "heading": "What the bundled catalog suggests",
                    "body": (
                        f"In the current bundled catalog, this family has {stats['count']} matched entries with a median recommended RAM of "
                        f"{stats['median_recommended_ram']:.1f}GB. The dominant architecture labels in this slice are {top_architectures}."
                    ),
                },
                {
                    "heading": "How to use the family intelligently",
                    "body": "Start with the family to set intent, then narrow by hardware fit, context goals, and runtime compatibility before you choose a specific build.",
                },
            ],
            "zh": [
                {
                    "heading": f"为什么围绕 {family_name} 的搜索需要适配层",
                    "body": (
                        f"用户搜索 {family_name} 时，通常先记住的是家族名，但真正决定部署成败的是内存、量化、上下文长度和运行时支持。"
                        "这篇页面的作用，就是把家族兴趣重新落到可执行的部署判断上。"
                    ),
                },
                {
                    "heading": "内置目录能说明什么",
                    "body": (
                        f"在当前内置目录中，这个家族共匹配到 {stats['count']} 个条目，建议内存中位数约为 {stats['median_recommended_ram']:.1f}GB。"
                        f"更常见的架构标签包括 {top_architectures or '多种架构混合'}。"
                    ),
                },
                {
                    "heading": "更聪明地使用家族名",
                    "body": "先用家族名收敛方向，再根据硬件适配、上下文目标和运行时兼容性缩小到具体构建版本。",
                },
            ],
        }
        metrics = {
            "en": [
                {"value": str(stats["count"]), "label": "catalog matches for this family"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "median recommended RAM across family entries"},
                {"value": f"{stats['median_context']:.0f}", "label": "median context length across the family slice"},
            ],
            "zh": [
                {"value": str(stats["count"]), "label": "该家族在目录中的匹配条目数"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "家族条目的建议内存中位数"},
                {"value": f"{stats['median_context']:.0f}", "label": "家族条目的上下文中位数"},
            ],
        }
    else:
        sections = {
            "en": [
                {
                    "heading": "Where convenience ends and planning begins",
                    "body": "Runtime tools make local AI easier to operate, but they do not answer whether the chosen model leaves enough headroom for the real workflow.",
                },
                {
                    "heading": "Why this still belongs on a professional site",
                    "body": "Teams repeatedly search for approachable explanations of runtimes, formats, and deployment paths. A useful site should answer that intent with fit-aware guidance instead of generic hype.",
                },
                {
                    "heading": "How to use LLMFit in the loop",
                    "body": "Use the runtime for execution, and use LLMFit before that point to decide which machine, model family, and memory budget are realistic.",
                },
            ],
            "zh": [
                {
                    "heading": "便利性止于哪里，规划从哪里开始",
                    "body": "运行时工具确实能让本地 AI 更易用，但它们并不会直接回答：这个模型是否还能给真实工作流留下足够余量。",
                },
                {
                    "heading": "为什么这类内容应该出现在专业站点里",
                    "body": "团队会反复搜索运行时、模型格式和部署路径。如果站点真的想承接这类流量，就应该提供带适配判断的解释，而不是泛化宣传。",
                },
                {
                    "heading": "如何把 LLMFit 放进流程里",
                    "body": "运行时负责执行，LLMFit 负责在执行之前先判断哪台机器、哪个模型家族和哪种内存预算更现实。",
                },
            ],
        }
        metrics = {
            "en": [
                {"value": str(stats["count"]), "label": "high-download catalog entries reviewed for this guide"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "median recommended RAM across the reference slice"},
                {"value": f"{stats['median_context']:.0f}", "label": "median context length across the reference slice"},
            ],
            "zh": [
                {"value": str(stats["count"]), "label": "本指南参考的高下载目录条目数"},
                {"value": f"{stats['median_recommended_ram']:.1f}GB", "label": "参考切片的建议内存中位数"},
                {"value": f"{stats['median_context']:.0f}", "label": "参考切片的上下文中位数"},
            ],
        }

    return {
        "slug": topic.slug,
        "kind": topic.kind,
        "topic_id": topic.topic_id,
        "title_en": topic.title_hint_en,
        "title_zh": topic.title_hint_zh,
        "description_en": topic.description_hint_en,
        "description_zh": topic.description_hint_zh,
        "lede_en": copy_payload["en"]["lede"],
        "lede_zh": copy_payload["zh"]["lede"],
        "why_en": copy_payload["en"]["why_it_matters"],
        "why_zh": copy_payload["zh"]["why_it_matters"],
        "takeaway_en": copy_payload["en"]["takeaway"],
        "takeaway_zh": copy_payload["zh"]["takeaway"],
        "faq_en": copy_payload["en"]["faq"],
        "faq_zh": copy_payload["zh"]["faq"],
        "sections_en": sections["en"],
        "sections_zh": sections["zh"],
        "metrics_en": metrics["en"],
        "metrics_zh": metrics["zh"],
        "examples": examples,
        "command": command,
        "label_en": label_en,
        "label_zh": label_zh,
        "stats": stats,
        "draft_mode": draft_mode,
        "draft_attempts": draft_result.attempts,
        "draft_error": draft_result.error,
        "draft_endpoint": llm_client.endpoint if llm_client else None,
    }


def topbar(locale: str, page_key: str, english_url: str, chinese_url: str) -> str:
    labels = EN_PAGE_LABELS if locale == "en" else ZH_PAGE_LABELS
    prefix = "" if locale == "en" else "/zh"
    brand_href = home_path(locale)
    return f"""
  <header class="topbar">
    <div class="topbar-shell">
      <a class="brand" href="{brand_href}">
        <img src="/assets/icon.svg" alt="LLMFit logo">
        <span>LLMFit</span>
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">{labels['menu']}</button>
      <nav class="nav" id="site-nav">
        <a data-page-link="home" href="{brand_href}">{labels['home']}</a>
        <a data-page-link="docs" href="{prefix}/docs/">{labels['docs']}</a>
        <a data-page-link="use-cases" href="{prefix}/use-cases/">{labels['use_cases']}</a>
        <a data-page-link="api" href="{prefix}/api/">{labels['api']}</a>
        <a data-page-link="self-host" href="{prefix}/self-host/">{labels['self_host']}</a>
        <a data-page-link="insights" href="{prefix}/insights/">{labels['insights']}</a>
        <a data-page-link="faq" href="{prefix}/faq/">{labels['faq']}</a>
        <div class="language-switcher" aria-label="Language switcher">
          <a data-lang-link="en" href="{english_url}">EN</a>
          <a data-lang-link="zh" href="{chinese_url}">中文</a>
        </div>
        <a class="nav-cta" href="https://github.com/miounet11/llmfit">{labels['github']}</a>
      </nav>
    </div>
  </header>
    """


def render_article(
    article: dict[str, Any],
    locale: str,
    site_url: str,
    articles: list[dict[str, Any]],
) -> str:
    is_en = locale == "en"
    lang = "en" if is_en else "zh-CN"
    title = article["title_en"] if is_en else article["title_zh"]
    description = article["description_en"] if is_en else article["description_zh"]
    lede = article["lede_en"] if is_en else article["lede_zh"]
    why_points = article["why_en"] if is_en else article["why_zh"]
    sections = article["sections_en"] if is_en else article["sections_zh"]
    metrics = article["metrics_en"] if is_en else article["metrics_zh"]
    faq = article["faq_en"] if is_en else article["faq_zh"]
    takeaway = article["takeaway_en"] if is_en else article["takeaway_zh"]
    label = article["label_en"] if is_en else article["label_zh"]
    published_on = article["published_on"]
    path = article_path(article, locale)
    english_url = article_path(article, "en")
    chinese_url = article_path(article, "zh")
    alternate_url = f"{site_url}{chinese_url if is_en else english_url}"
    canonical_url = f"{site_url}{path}"
    rss_url = f"{site_url}{feed_path(locale)}"
    kind_path = kind_index_path(article["kind"], locale)
    kind_title = kind_label(article["kind"], locale)
    heading_why = "Why this page is worth reading" if is_en else "为什么这篇页面值得看"
    heading_examples = "Representative catalog examples" if is_en else "代表性目录示例"
    heading_verify = "How to verify this on your own machine" if is_en else "如何在自己的机器上验证"
    heading_takeaway = "Operational takeaway" if is_en else "运营建议"
    heading_faq = "Frequently asked questions" if is_en else "常见问题"
    heading_related = "Related pages" if is_en else "相关页面"
    related_title = "Continue from this topic cluster" if is_en else "从这个主题集群继续深入"
    heading_back = "Back to insights" if is_en else "返回洞察中心"
    breadcrumb_home = "Insights" if is_en else "洞察"
    notes = (
        "This article is generated from a curated topic pool and the bundled LLMFit model catalog. It is intended as fit-aware editorial guidance, not as a guaranteed benchmark."
        if is_en
        else "这篇内容基于受控主题池和 LLMFit 内置模型目录生成，目标是提供带适配判断的编辑型内容，而不是承诺型 Benchmark 结论。"
    )

    example_markup = "\n".join(example_card(entry, locale) for entry in article["examples"])
    metrics_markup = "\n".join(
        f"""          <article class="metric-card"><strong>{html.escape(item['value'])}</strong><span>{html.escape(item['label'])}</span></article>"""
        for item in metrics
    )
    why_markup = "\n".join(f"            <li>{html.escape(point)}</li>" for point in why_points)
    section_markup = "\n".join(
        f"""
        <article class="content-card">
          <h3>{html.escape(section['heading'])}</h3>
          <p>{html.escape(section['body'])}</p>
        </article>
        """
        for section in sections
    )
    faq_markup = "\n".join(
        f"""
      <details{" open" if index == 0 else ""}>
        <summary>{html.escape(item['q'])}</summary>
        <p>{html.escape(item['a'])}</p>
      </details>
        """
        for index, item in enumerate(faq)
    )
    published_label = "Published" if is_en else "发布日期"
    focus_label = "Focus" if is_en else "聚焦主题"
    related_cards = [article_link_card(item, locale) for item in select_related_articles(article, articles)]
    browse_copy = (
        f"See every {kind_title.lower()} page in the insight library."
        if is_en
        else f"查看洞察库中全部“{kind_title}”页面。"
    )
    related_cards.append(
        f"""
        <a class="link-card category-card" href="{kind_path}">
          <div class="card-meta">
            <span class="section-pill">{html.escape(kind_title)}</span>
            <em>{html.escape('Browse cluster' if is_en else '浏览主题集群')}</em>
          </div>
          <strong>{html.escape('Open the category hub' if is_en else '打开分类中心')}</strong>
          <span>{html.escape(browse_copy)}</span>
          <p class="card-caption">{html.escape(kind_path)}</p>
        </a>
        """
    )
    related_markup = "\n".join(related_cards)

    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "description": description,
        "datePublished": published_on,
        "dateModified": published_on,
        "author": {"@type": "Organization", "name": "LLMFit"},
        "publisher": {"@type": "Organization", "name": "LLMFit"},
        "mainEntityOfPage": canonical_url,
        "about": label,
        "inLanguage": lang,
    }

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | LLMFit</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" hreflang="en" href="{site_url}{english_url}">
  <link rel="alternate" hreflang="zh-CN" href="{site_url}{chinese_url}">
  <link rel="alternate" hreflang="x-default" href="{site_url}{english_url}">
  <link rel="alternate" type="application/rss+xml" title="LLMFit Insights RSS" href="{rss_url}">
  <link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/styles.css">
</head>
<body data-page="insights">
  <div class="background-glow background-glow-a"></div>
  <div class="background-glow background-glow-b"></div>
{topbar(locale, "insights", english_url, chinese_url)}
  <main>
    <section class="page-hero reveal">
      <p class="eyebrow">{breadcrumb_home}</p>
      <h1>{html.escape(title)}</h1>
      <p class="lede">{html.escape(lede)}</p>
      <div class="article-meta">
        <span>{published_label}: {html.escape(published_on)}</span>
        <span>{focus_label}: {html.escape(label)}</span>
      </div>
    </section>

    <section class="section reveal">
      <div class="kpi-grid">
{metrics_markup}
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{heading_why}</p>
          <h2>{html.escape(title)}</h2>
        </div>
      </div>
      <div class="callout">
        <p>{html.escape(notes)}</p>
      </div>
      <div class="content-card article-list-card">
        <ul class="checklist article-list">
{why_markup}
        </ul>
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{heading_examples}</p>
          <h2>{html.escape(label)}</h2>
        </div>
      </div>
      <div class="card-grid">
{example_markup}
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{heading_verify}</p>
          <h2>LLMFit</h2>
        </div>
      </div>
      <div class="code-grid">
        <article class="content-card">
          <h3>CLI</h3>
          <pre class="code-block"><code>{html.escape(article['command'])}</code></pre>
        </article>
        <article class="content-card">
          <h3>{heading_takeaway}</h3>
          <p>{html.escape(takeaway)}</p>
        </article>
      </div>
      <div class="detail-grid">
{section_markup}
      </div>
    </section>

    <section class="section reveal faq-list">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{heading_faq}</p>
          <h2>{html.escape(title)}</h2>
        </div>
      </div>
{faq_markup}
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{heading_related}</p>
          <h2>{html.escape(related_title)}</h2>
        </div>
      </div>
      <div class="link-grid insights-grid">
{related_markup}
      </div>
    </section>

    <section class="section section-cta reveal">
      <div>
        <p class="eyebrow">{breadcrumb_home}</p>
        <h2>{heading_back}</h2>
      </div>
      <div class="cta-actions">
        <a class="button button-primary" href="{'/insights/' if is_en else '/zh/insights/'}">{heading_back}</a>
        <a class="button button-secondary" href="{'/docs/' if is_en else '/zh/docs/'}">{'Read the docs' if is_en else '阅读文档'}</a>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div>
      <strong>LLMFit {breadcrumb_home}</strong>
      <p>{'Original, fit-aware content for teams evaluating local AI deployments.' if is_en else '为评估本地 AI 部署的团队提供原创且带适配判断的内容。'}</p>
    </div>
    <div class="footer-links">
      <a href="{'/insights/' if is_en else '/zh/insights/'}">{breadcrumb_home}</a>
      <a href="{'/docs/' if is_en else '/zh/docs/'}">{'Docs' if is_en else '文档'}</a>
      <a href="{'/api/' if is_en else '/zh/api/'}">API</a>
      <a href="{'/faq/' if is_en else '/zh/faq/'}">{'FAQ' if is_en else '常见问题'}</a>
    </div>
    <p><span class="year"></span> miounet11/llmfit</p>
  </footer>

  <script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
  </script>
  <script src="/app.js"></script>
</body>
</html>
"""


def render_index(locale: str, articles: list[dict[str, Any]], site_url: str) -> str:
    is_en = locale == "en"
    title = "LLMFit Insights | Daily local AI fit content for builders and platform teams" if is_en else "LLMFit 洞察 | 每日更新的本地 AI 适配内容中心"
    description = (
        "A growing library of original pages about local AI model fit, hardware sizing, runtime choices, and deployment planning."
        if is_en
        else "围绕本地 AI 模型适配、硬件规划、运行时选择和部署判断持续更新的原创内容库。"
    )
    path = "/insights/" if is_en else "/zh/insights/"
    english_url = "/insights/"
    chinese_url = "/zh/insights/"
    rss_url = f"{site_url}{feed_path(locale)}"
    category_cards = "\n".join(kind_card(kind, locale, articles) for kind in KIND_META)
    cards_markup = "\n".join(article_link_card(article, locale) for article in articles) if articles else ""
    return f"""<!doctype html>
<html lang="{'en' if is_en else 'zh-CN'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{site_url}{path}">
  <link rel="alternate" hreflang="en" href="{site_url}{english_url}">
  <link rel="alternate" hreflang="zh-CN" href="{site_url}{chinese_url}">
  <link rel="alternate" hreflang="x-default" href="{site_url}{english_url}">
  <link rel="alternate" type="application/rss+xml" title="LLMFit Insights RSS" href="{rss_url}">
  <link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/styles.css">
</head>
<body data-page="insights">
  <div class="background-glow background-glow-a"></div>
  <div class="background-glow background-glow-b"></div>
{topbar(locale, "insights", english_url, chinese_url)}
  <main>
    <section class="page-hero reveal">
      <p class="eyebrow">{'Insights' if is_en else '洞察'}</p>
      <h1>{'A programmatic content library for local AI deployment decisions.' if is_en else '围绕本地 AI 部署决策持续扩展的内容中心。'}</h1>
      <p class="lede">{html.escape(description)}</p>
      <div class="callout">
        <p>{'These pages are generated from a curated topic pool tied to LLMFit themes: hardware fit, runtime choice, deployment planning, and model-family search intent.' if is_en else '这些页面基于受控主题池生成，主题严格围绕 LLMFit 的核心方向：硬件适配、运行时选择、部署规划和模型家族搜索意图。'}</p>
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{'Topic clusters' if is_en else '主题集群'}</p>
          <h2>{'Browse the content library by decision type.' if is_en else '按决策类型浏览内容库。'}</h2>
        </div>
      </div>
      <div class="link-grid insights-grid">
{category_cards}
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{'Latest pages' if is_en else '最新页面'}</p>
          <h2>{'Original pages published from the site engine.' if is_en else '由站点内容引擎发布的原创页面。'}</h2>
        </div>
      </div>
      <div class="link-grid insights-grid">
{cards_markup}
      </div>
    </section>

    <section class="section section-cta reveal">
      <div>
        <p class="eyebrow">{'Next step' if is_en else '下一步'}</p>
        <h2>{'Use the library to capture search intent, then route serious users into docs and product workflows.' if is_en else '先用内容承接搜索意图，再把真正有需求的用户导向文档和产品工作流。'}</h2>
      </div>
      <div class="cta-actions">
        <a class="button button-primary" href="{'/docs/' if is_en else '/zh/docs/'}">{'Read the docs' if is_en else '阅读文档'}</a>
        <a class="button button-secondary" href="{'/use-cases/' if is_en else '/zh/use-cases/'}">{'See use cases' if is_en else '查看应用场景'}</a>
        <a class="button button-secondary" href="{feed_path(locale)}">{'Subscribe via RSS' if is_en else '通过 RSS 订阅'}</a>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div>
      <strong>LLMFit {'Insights' if is_en else '洞察'}</strong>
      <p>{'Original pages designed to win relevant traffic without drifting outside the product theme.' if is_en else '在不偏离产品主题的前提下，为站点获取更相关搜索流量的原创内容。'}</p>
    </div>
    <div class="footer-links">
      <a href="{path}">{'Insights' if is_en else '洞察'}</a>
      <a href="{'/docs/' if is_en else '/zh/docs/'}">{'Docs' if is_en else '文档'}</a>
      <a href="{'/api/' if is_en else '/zh/api/'}">API</a>
      <a href="{'/faq/' if is_en else '/zh/faq/'}">{'FAQ' if is_en else '常见问题'}</a>
    </div>
    <p><span class="year"></span> miounet11/llmfit</p>
  </footer>

  <script src="/app.js"></script>
</body>
</html>
"""


def render_kind_index(kind: str, locale: str, articles: list[dict[str, Any]], site_url: str) -> str:
    is_en = locale == "en"
    lang = "en" if is_en else "zh-CN"
    meta = KIND_META[kind]
    key_title = "title_en" if is_en else "title_zh"
    key_description = "description_en" if is_en else "description_zh"
    key_intro = "intro_en" if is_en else "intro_zh"
    filtered = [article for article in articles if article.get("kind") == kind]
    peer_cards = "\n".join(kind_card(peer_kind, locale, articles) for peer_kind in KIND_META if peer_kind != kind)
    cards_markup = "\n".join(article_link_card(article, locale) for article in filtered)
    canonical_path = kind_index_path(kind, locale)
    english_url = kind_index_path(kind, "en")
    chinese_url = kind_index_path(kind, "zh")
    rss_url = f"{site_url}{feed_path(locale)}"
    focus_values = {article["label_en"] if is_en else article["label_zh"] for article in filtered}
    latest_value = filtered[0]["published_on"] if filtered else ("Not published yet" if is_en else "暂未发布")
    published_label = "Latest publication" if is_en else "最近发布日期"
    count_label = "Published pages" if is_en else "已发布页面"
    focus_label = "Distinct focus areas" if is_en else "覆盖细分主题"
    section_heading = "Pages in this cluster" if is_en else "该分类下的页面"
    section_title = "Structured pages you can browse or feed into product onboarding." if is_en else "可浏览、也可导入产品转化路径的结构化页面。"
    adjacent_heading = "Adjacent clusters" if is_en else "相邻主题集群"
    adjacent_title = "Use nearby categories to expand the decision path." if is_en else "用相邻分类扩展用户的决策路径。"
    cta_title = "Move from content into evaluation." if is_en else "从内容浏览进入产品评估。"
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "headline": meta[key_title],
        "description": meta[key_description],
        "inLanguage": lang,
        "isPartOf": f"{site_url}{'/insights/' if is_en else '/zh/insights/'}",
        "mainEntityOfPage": f"{site_url}{canonical_path}",
    }

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(str(meta[key_title]))} | LLMFit</title>
  <meta name="description" content="{html.escape(str(meta[key_description]))}">
  <link rel="canonical" href="{site_url}{canonical_path}">
  <link rel="alternate" hreflang="en" href="{site_url}{english_url}">
  <link rel="alternate" hreflang="zh-CN" href="{site_url}{chinese_url}">
  <link rel="alternate" hreflang="x-default" href="{site_url}{english_url}">
  <link rel="alternate" type="application/rss+xml" title="LLMFit Insights RSS" href="{rss_url}">
  <link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/styles.css">
</head>
<body data-page="insights">
  <div class="background-glow background-glow-a"></div>
  <div class="background-glow background-glow-b"></div>
{topbar(locale, "insights", english_url, chinese_url)}
  <main>
    <section class="page-hero reveal">
      <p class="eyebrow">{html.escape(kind_label(kind, locale))}</p>
      <h1>{html.escape(str(meta[key_title]))}</h1>
      <p class="lede">{html.escape(str(meta[key_description]))}</p>
      <div class="callout">
        <p>{html.escape(str(meta[key_intro]))}</p>
      </div>
    </section>

    <section class="section reveal">
      <div class="kpi-grid">
        <article class="metric-card"><strong>{len(filtered)}</strong><span>{count_label}</span></article>
        <article class="metric-card"><strong>{html.escape(latest_value)}</strong><span>{published_label}</span></article>
        <article class="metric-card"><strong>{len(focus_values)}</strong><span>{focus_label}</span></article>
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{html.escape(kind_label(kind, locale))}</p>
          <h2>{html.escape(section_title)}</h2>
        </div>
      </div>
      <div class="link-grid insights-grid">
{cards_markup}
      </div>
    </section>

    <section class="section reveal">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{adjacent_heading}</p>
          <h2>{adjacent_title}</h2>
        </div>
      </div>
      <div class="link-grid insights-grid">
{peer_cards}
      </div>
    </section>

    <section class="section section-cta reveal">
      <div>
        <p class="eyebrow">{section_heading}</p>
        <h2>{cta_title}</h2>
      </div>
      <div class="cta-actions">
        <a class="button button-primary" href="{'/docs/' if is_en else '/zh/docs/'}">{'Read the docs' if is_en else '阅读文档'}</a>
        <a class="button button-secondary" href="{'/insights/' if is_en else '/zh/insights/'}">{'All insights' if is_en else '全部洞察'}</a>
        <a class="button button-secondary" href="{feed_path(locale)}">{'RSS feed' if is_en else 'RSS 订阅'}</a>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div>
      <strong>LLMFit {html.escape(kind_label(kind, locale))}</strong>
      <p>{'Structured category pages for local AI operators, builders, and infrastructure teams.' if is_en else '为本地 AI 运营者、开发者和基础设施团队准备的结构化分类页面。'}</p>
    </div>
    <div class="footer-links">
      <a href="{'/insights/' if is_en else '/zh/insights/'}">{'Insights' if is_en else '洞察'}</a>
      <a href="{canonical_path}">{html.escape(kind_label(kind, locale))}</a>
      <a href="{'/docs/' if is_en else '/zh/docs/'}">{'Docs' if is_en else '文档'}</a>
      <a href="{'/faq/' if is_en else '/zh/faq/'}">{'FAQ' if is_en else '常见问题'}</a>
    </div>
    <p><span class="year"></span> miounet11/llmfit</p>
  </footer>

  <script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
  </script>
  <script src="/app.js"></script>
</body>
</html>
"""


def render_feed(locale: str, articles: list[dict[str, Any]], site_url: str) -> str:
    is_en = locale == "en"
    feed_title = "LLMFit Insights" if is_en else "LLMFit 洞察"
    feed_link = f"{site_url}{'/insights/' if is_en else '/zh/insights/'}"
    items = []
    for article in articles[:20]:
        title = article["title_en"] if is_en else article["title_zh"]
        description = article["description_en"] if is_en else article["description_zh"]
        path = f"/insights/{article['slug']}/" if is_en else f"/zh/insights/{article['slug']}/"
        pub_date = dt.datetime.strptime(article["published_on"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        items.append(
            f"""
    <item>
      <title>{xml_escape(title)}</title>
      <link>{xml_escape(site_url + path)}</link>
      <guid>{xml_escape(site_url + path)}</guid>
      <description>{xml_escape(description)}</description>
      <pubDate>{pub_date}</pubDate>
    </item>
            """
        )
    items_markup = "".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{xml_escape(feed_title)}</title>
    <link>{xml_escape(feed_link)}</link>
    <description>{xml_escape('Original fit-aware local AI content from LLMFit.' if is_en else '来自 LLMFit 的原创本地 AI 适配内容。')}</description>
{items_markup}
  </channel>
</rss>
"""


def render_sitemap(site_url: str, manifest_articles: list[dict[str, Any]]) -> str:
    urls = []
    for en_path, zh_path in STATIC_ROUTES:
        urls.append((en_path, 1.0 if en_path == "/" else 0.9 if en_path in {"/docs/", "/use-cases/", "/api/"} else 0.8))
        urls.append((zh_path, 1.0 if zh_path == "/zh/" else 0.9 if zh_path in {"/zh/docs/", "/zh/use-cases/", "/zh/api/"} else 0.8))
    for article in manifest_articles:
        urls.append((f"/insights/{article['slug']}/", 0.7))
        urls.append((f"/zh/insights/{article['slug']}/", 0.7))
    unique_urls = []
    seen = set()
    for path, priority in urls:
        if path in seen:
            continue
        seen.add(path)
        unique_urls.append((path, priority))

    body = []
    for path, priority in unique_urls:
        body.append(
            f"""  <url>\n    <loc>{xml_escape(site_url + path)}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>{priority:.1f}</priority>\n  </url>"""
        )
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + "\n".join(body) + "\n</urlset>\n"


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "articles": []}
    with path.open() as handle:
        return json.load(handle)


def select_topics(pool: list[Topic], manifest: dict[str, Any], count: int) -> list[Topic]:
    published = {article["topic_id"] for article in manifest.get("articles", [])}
    remaining = [topic for topic in pool if topic.topic_id not in published]
    selected: list[Topic] = []
    used_ids: set[str] = set()
    selected_by_kind: Counter[str] = Counter()

    quotas = {"hardware": 2, "family": 1, "runtime": 0}
    if count >= 4:
        quotas["runtime"] = 1
    if count >= 5:
        quotas["hardware"] = 3

    for kind, quota in quotas.items():
        for topic in remaining:
            if len(selected) >= count:
                return selected
            if selected_by_kind[kind] >= quota:
                break
            if topic.kind != kind or topic.topic_id in used_ids:
                continue
            selected.append(topic)
            used_ids.add(topic.topic_id)
            selected_by_kind[kind] += 1

    for topic in remaining:
        if len(selected) >= count:
            break
        if topic.topic_id in used_ids:
            continue
        selected.append(topic)
        used_ids.add(topic.topic_id)
        selected_by_kind[topic.kind] += 1

    return selected


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def ensure_manifest_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_run_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate bilingual site content pages for LLMFit.")
    parser.add_argument("--repo-root", default=None, help="Repository root. Defaults to the parent of this script.")
    parser.add_argument("--site-root", default="site", help="Site directory to write into.")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help="Manifest/state file.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="How many new topics to publish in this run.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Publication date in YYYY-MM-DD format.")
    parser.add_argument("--site-url", default=os.environ.get("LLMFIT_CONTENT_SITE_BASE_URL", DEFAULT_SITE_URL))
    parser.add_argument("--llm-endpoint", default=os.environ.get("LLMFIT_CONTENT_LLM_ENDPOINT"))
    parser.add_argument("--llm-api-key", default=os.environ.get("LLMFIT_CONTENT_LLM_API_KEY"))
    parser.add_argument("--llm-model", default=os.environ.get("LLMFIT_CONTENT_LLM_MODEL", "auto"))
    parser.add_argument("--llm-timeout", type=int, default=int(os.environ.get("LLMFIT_CONTENT_LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT)))
    parser.add_argument("--llm-retries", type=int, default=int(os.environ.get("LLMFIT_CONTENT_LLM_RETRIES", DEFAULT_LLM_RETRIES)))
    parser.add_argument(
        "--llm-retry-delay-seconds",
        type=float,
        default=float(os.environ.get("LLMFIT_CONTENT_LLM_RETRY_DELAY_SECONDS", DEFAULT_LLM_RETRY_DELAY_SECONDS)),
    )
    parser.add_argument("--report-file", default=os.environ.get("LLMFIT_CONTENT_RUN_REPORT_FILE"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    site_root = Path(args.site_root)
    if not site_root.is_absolute():
        site_root = (repo_root / site_root).resolve()
    state_file = Path(args.state_file)
    if not state_file.is_absolute():
        state_file = (repo_root / state_file).resolve()
    report_file = Path(args.report_file) if args.report_file else None
    if report_file and not report_file.is_absolute():
        report_file = (repo_root / report_file).resolve()

    catalog = load_catalog(repo_root)
    topic_pool = build_topic_pool(catalog)
    ensure_manifest_parent(state_file)
    manifest = load_manifest(state_file)
    llm_client = None
    if args.llm_endpoint and args.llm_api_key:
        llm_client = LLMClient(
            args.llm_endpoint,
            args.llm_api_key,
            args.llm_model,
            timeout=args.llm_timeout,
            retries=args.llm_retries,
            retry_delay_seconds=args.llm_retry_delay_seconds,
        )

    selected = select_topics(topic_pool, manifest, max(1, min(args.count, 5)))

    articles = copy.deepcopy(manifest.get("articles", []))
    published_date = args.date
    drafted_articles: list[dict[str, Any]] = []
    run_started_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    for topic in selected:
        article = build_article_data(topic, catalog, llm_client)
        article["published_on"] = published_date
        drafted_articles.append(article)
        print(f"drafted {article['slug']} via {article['draft_mode']}")
        if article["draft_mode"] != "llm" and article.get("draft_error") and llm_client:
            print(f"[content-llm] fallback for {article['slug']}: {article['draft_error']}")

    articles.extend(drafted_articles)
    articles = sorted(articles, key=lambda item: (item["published_on"], item["slug"]), reverse=True)
    manifest["articles"] = articles
    state_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    for article in articles:
        write_text(site_root / "insights" / article["slug"] / "index.html", render_article(article, "en", args.site_url.rstrip("/"), articles))
        write_text(site_root / "zh" / "insights" / article["slug"] / "index.html", render_article(article, "zh", args.site_url.rstrip("/"), articles))

    write_text(site_root / "insights" / "index.html", render_index("en", articles, args.site_url.rstrip("/")))
    write_text(site_root / "zh" / "insights" / "index.html", render_index("zh", articles, args.site_url.rstrip("/")))
    for kind in KIND_META:
        write_text(site_root / "insights" / KIND_META[kind]["slug"] / "index.html", render_kind_index(kind, "en", articles, args.site_url.rstrip("/")))
        write_text(site_root / "zh" / "insights" / KIND_META[kind]["slug"] / "index.html", render_kind_index(kind, "zh", articles, args.site_url.rstrip("/")))
    write_text(site_root / "feed.xml", render_feed("en", articles, args.site_url.rstrip("/")))
    write_text(site_root / "zh" / "feed.xml", render_feed("zh", articles, args.site_url.rstrip("/")))
    write_text(site_root / "sitemap.xml", render_sitemap(args.site_url.rstrip("/"), articles))

    llm_success_count = sum(1 for article in drafted_articles if article["draft_mode"] == "llm")
    fallback_articles = [
        {
            "slug": article["slug"],
            "error": article.get("draft_error"),
            "attempts": article.get("draft_attempts"),
        }
        for article in drafted_articles
        if article["draft_mode"] != "llm"
    ]
    run_report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "run_started_at": run_started_at,
        "publish_date": published_date,
        "site_url": args.site_url.rstrip("/"),
        "selected_count": len(selected),
        "published_count": len(drafted_articles),
        "llm_enabled": bool(llm_client),
        "llm_endpoint": llm_client.endpoint if llm_client else None,
        "llm_model": args.llm_model if llm_client else None,
        "llm_timeout_seconds": args.llm_timeout if llm_client else None,
        "llm_retries": args.llm_retries if llm_client else None,
        "llm_success_count": llm_success_count,
        "fallback_count": len(fallback_articles),
        "topics": [
            {
                "slug": article["slug"],
                "topic_id": article["topic_id"],
                "kind": article["kind"],
                "draft_mode": article["draft_mode"],
                "draft_attempts": article.get("draft_attempts"),
                "draft_error": article.get("draft_error"),
            }
            for article in drafted_articles
        ],
        "fallback_topics": fallback_articles,
    }
    if report_file:
        write_run_report(report_file, run_report)
        print(f"run report written to {report_file}")

    print(
        "llm summary: "
        f"{llm_success_count} llm, "
        f"{len(fallback_articles)} fallback, "
        f"{'enabled' if llm_client else 'disabled'}"
    )
    print(f"published {len(drafted_articles)} new topics")
    for topic in selected:
        print(f"- {topic.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
