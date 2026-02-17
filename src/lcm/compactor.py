from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import httpx

from .store import Message


class Compactor:
    """Three-stage compactor with deterministic fallback and optional Kimi-backed LLM compression."""

    def __init__(
        self,
        *,
        token_counter: Callable[[str], int] | None = None,
        model: str = "kimi-k2.5",
        api_base: str = "https://api.moonshot.cn/v1",
        api_key: str | None = None,
        timeout: float = 20.0,
    ):
        self.token_counter = token_counter or self._default_token_counter
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        disable_llm = os.getenv("LCM_DISABLE_LLM", "0") == "1"
        self.api_key = None if disable_llm else (api_key or os.getenv("KIMI_API_KEY") or self._load_key_from_openviking_config())
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
    def _load_key_from_openviking_config() -> str | None:
        cfg = Path("/home/ubuntu/.openviking/ov.conf")
        if not cfg.exists():
            return None
        try:
            content = json.loads(cfg.read_text(encoding="utf-8"))
            return content.get("vlm", {}).get("api_key")
        except Exception:
            return None

    def count_messages_tokens(self, messages: list[Message]) -> int:
        return sum(self.token_counter(m.content) for m in messages)

    def _build_source_text(self, messages: list[Message]) -> str:
        return "\n".join(f"{m.role}: {m.content.strip()}" for m in messages if m.content.strip())

    def _llm_compress(self, messages: list[Message], style: str, max_tokens: int) -> str:
        if not self.api_key:
            raise RuntimeError("Kimi API key is not configured")

        source = self._build_source_text(messages)
        if style == "aggressive":
            system = "你是记忆压缩器。将以下对话极度压缩为要点列表，只保留最核心的事实和决策。用中文输出。"
        elif style == "normal":
            system = "你是记忆压缩器。将以下对话压缩为详细摘要，保留所有关键事实、人名、技术细节、决策和数字。用中文输出。"
        else:
            system = "你是记忆压缩器。保留关键信息，压缩冗余。用中文输出。"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"请压缩以下对话：\n\n{source}"},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        url = f"{self.api_base}/chat/completions"
        resp = self._client.post(
            url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if resp.status_code >= 400 and "only 1 is allowed" in resp.text:
            payload["temperature"] = 1
            resp = self._client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        import time
        time.sleep(2)
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
