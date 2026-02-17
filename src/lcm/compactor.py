from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import httpx

from .store import Message


class Compactor:
    """Three-stage compactor with deterministic fallback and optional Gemini-backed LLM compression."""

    def __init__(
        self,
        *,
        token_counter: Callable[[str], int] | None = None,
        model: str = "gemini-2.5-flash",
        api_base: str = "https://generativelanguage.googleapis.com/v1beta/openai",
        api_key: str | None = None,
        timeout: float = 20.0,
    ):
        self.token_counter = token_counter or self._default_token_counter
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        disable_llm = os.getenv("LCM_DISABLE_LLM", "0") == "1"
        self.api_key = None if disable_llm else (api_key or os.getenv("GEMINI_API_KEY") or self._load_key_from_openclaw_config())
        self._client = httpx.Client(timeout=self.timeout)
        self.compress_stats: dict[str, int] = {
            "normal": 0,
            "aggressive": 0,
            "deterministic_fallback": 0,
        }

    @staticmethod
    def _default_token_counter(text: str) -> int:
        return max(1, len(text.split())) if text.strip() else 0

    @staticmethod
    def _load_key_from_openclaw_config() -> str | None:
        cfg = Path("/home/ubuntu/.openclaw/openclaw.json")
        if not cfg.exists():
            return None
        try:
            content = json.loads(cfg.read_text(encoding="utf-8"))
            return content["models"]["providers"]["google-free-3"]["apiKey"]
        except Exception:
            return None

    def count_messages_tokens(self, messages: list[Message]) -> int:
        return sum(self.token_counter(m.content) for m in messages)

    def _build_source_text(self, messages: list[Message]) -> str:
        return "\n".join(f"{m.role}: {m.content.strip()}" for m in messages if m.content.strip())

    def _llm_compress(self, messages: list[Message], style: str, max_tokens: int) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured")

        source = self._build_source_text(messages)
        instruction = (
            "You are a context compactor for long conversation memory. "
            f"Produce a {style} summary under {max_tokens} words. "
            "Preserve key facts, decisions, constraints, names, numbers, and unresolved TODOs. "
            "Use concise plain text only."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": source},
            ],
            "temperature": 0.1,
        }
        url = f"{self.api_base}/chat/completions"
        resp = self._client.post(url, headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return f"[{style.upper()}] {text}"

    def normal_compress(self, messages: list[Message], target_tokens: int | None = None) -> str:
        budget = max(80, target_tokens or 220)
        try:
            return self._llm_compress(messages, style="normal", max_tokens=budget)
        except Exception:
            merged = " ".join(m.content.strip() for m in messages if m.content.strip())
            words = merged.split()
            keep = min(120, len(words))
            return "[NORMAL] " + " ".join(words[:keep])

    def aggressive_compress(self, messages: list[Message], target_tokens: int | None = None) -> str:
        budget = max(40, target_tokens or 120)
        try:
            return self._llm_compress(messages, style="aggressive", max_tokens=budget)
        except Exception:
            bullets = []
            for msg in messages:
                first = msg.content.strip().split(".")[0][:120]
                if first:
                    bullets.append(f"- ({msg.role}) {first}")
            return "[AGGRESSIVE]\n" + "\n".join(bullets[:12])

    def deterministic_fallback(self, messages: list[Message], max_tokens: int) -> str:
        if max_tokens <= 0:
            return "[FALLBACK]"

        chunks = [f"{m.role}: {m.content}" for m in messages]
        all_words = " ".join(chunks).split()
        if len(all_words) <= max_tokens:
            return "[FALLBACK] " + " ".join(all_words)

        if max_tokens <= 4:
            return "[FALLBACK] " + " ".join(all_words[:max_tokens])

        head_n = max_tokens // 2
        tail_n = max_tokens - head_n - 1
        head = all_words[:head_n]
        tail = all_words[-tail_n:] if tail_n > 0 else []
        return "[FALLBACK] " + " ".join(head + ["..."] + tail)

    def compress(self, messages: list[Message], target_tokens: int) -> tuple[str, str]:
        normal = self.normal_compress(messages, target_tokens=target_tokens)
        if self.token_counter(normal) <= target_tokens:
            self.compress_stats["normal"] += 1
            return "normal", normal

        aggressive = self.aggressive_compress(messages, target_tokens=target_tokens)
        if self.token_counter(aggressive) <= target_tokens:
            self.compress_stats["aggressive"] += 1
            return "aggressive", aggressive

        fallback = self.deterministic_fallback(messages, max_tokens=target_tokens)
        while self.token_counter(fallback) > target_tokens and target_tokens > 1:
            target_tokens -= 1
            fallback = self.deterministic_fallback(messages, max_tokens=target_tokens)
        self.compress_stats["deterministic_fallback"] += 1
        return "deterministic_fallback", fallback
