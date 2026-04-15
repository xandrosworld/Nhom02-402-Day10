"""
Provider helpers for Day 10 extensions.

- Embeddings: Voyage (preferred) or local SentenceTransformers fallback.
- LLM judge: Claudible via Anthropic-compatible endpoint.
"""

from __future__ import annotations

import json
import os
from typing import Any, Sequence

from dotenv import load_dotenv

load_dotenv()


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    raise json.JSONDecodeError("Unterminated JSON object", text, start)


class VoyageEmbeddingFunction:
    """Chroma-compatible embedding function backed by Voyage AI."""

    def __init__(self, *, api_key: str, model_name: str) -> None:
        import voyageai

        self._client = voyageai.Client(api_key=api_key)
        self._model_name = model_name

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        texts = list(input)
        if not texts:
            return []
        result = self._client.embed(texts, model=self._model_name)
        return [list(vec) for vec in result.embeddings]

    def name(self) -> str:
        return f"voyage::{self._model_name}"

    def embed_documents(self, input: Sequence[str]) -> list[list[float]]:
        return self.__call__(input)

    def embed_query(self, input: Sequence[str]) -> list[list[float]]:
        return self.__call__(input)


def get_embedding_provider() -> str:
    return os.environ.get("EMBEDDING_PROVIDER", "voyage").strip().lower()


def get_embedding_model_name() -> str:
    provider = get_embedding_provider()
    if provider == "voyage":
        return os.environ.get("VOYAGE_EMBEDDING_MODEL", "voyage-multilingual-2")
    return os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def get_chroma_embedding_function():
    provider = get_embedding_provider()

    if provider == "voyage":
        api_key = os.environ.get("VOYAGE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("EMBEDDING_PROVIDER=voyage nhưng thiếu VOYAGE_API_KEY.")
        return VoyageEmbeddingFunction(
            api_key=api_key,
            model_name=get_embedding_model_name(),
        )

    if provider in {"sentence_transformers", "local", "st"}:
        from chromadb.utils import embedding_functions

        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=get_embedding_model_name()
        )

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={provider!r}")


def get_llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "claudible").strip().lower()


def get_llm_model_name() -> str:
    return (
        os.environ.get("CLAUDIBLE_MODEL", "").strip()
        or os.environ.get("LLM_MODEL", "").strip()
        or "claude-sonnet-4.6"
    )


def _get_claudible_client():
    from openai import OpenAI

    api_key = (
        os.environ.get("CLAUDIBLE_API_KEY", "").strip()
        or os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
        or os.environ.get("ANTHROPIC_API_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError("Thiếu CLAUDIBLE_API_KEY hoặc ANTHROPIC_AUTH_TOKEN.")

    base_url = (
        os.environ.get("CLAUDIBLE_BASE_URL", "").strip()
        or os.environ.get("ANTHROPIC_BASE_URL", "").strip()
        or "https://claudible.io/v1"
    )
    return OpenAI(api_key=api_key, base_url=base_url)


def call_llm_text(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> str:
    provider = get_llm_provider()
    if provider != "claudible":
        raise ValueError(f"Unsupported LLM_PROVIDER={provider!r}")

    client = _get_claudible_client()
    response = client.chat.completions.create(
        model=get_llm_model_name(),
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def call_llm_json(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> dict[str, Any]:
    raw = call_llm_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return json.loads(_extract_first_json_object(cleaned))
