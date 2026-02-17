from __future__ import annotations

from typing import Callable

from .store import Message


class Compactor:
    """Three-stage compactor with guaranteed deterministic convergence."""

    def __init__(self, *, token_counter: Callable[[str], int] | None = None):
        self.token_counter = token_counter or self._default_token_counter

    @staticmethod
    def _default_token_counter(text: str) -> int:
        return max(1, len(text.split())) if text.strip() else 0

    def count_messages_tokens(self, messages: list[Message]) -> int:
        return sum(self.token_counter(m.content) for m in messages)

    def normal_compress(self, messages: list[Message]) -> str:
        merged = " ".join(m.content.strip() for m in messages if m.content.strip())
        words = merged.split()
        keep = min(120, len(words))
        return "[NORMAL] " + " ".join(words[:keep])

    def aggressive_compress(self, messages: list[Message]) -> str:
        bullets = []
        for i, msg in enumerate(messages, 1):
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
        normal = self.normal_compress(messages)
        if self.token_counter(normal) <= target_tokens:
            return "normal", normal

        aggressive = self.aggressive_compress(messages)
        if self.token_counter(aggressive) <= target_tokens:
            return "aggressive", aggressive

        fallback = self.deterministic_fallback(messages, max_tokens=target_tokens)
        while self.token_counter(fallback) > target_tokens and target_tokens > 1:
            target_tokens -= 1
            fallback = self.deterministic_fallback(messages, max_tokens=target_tokens)
        return "deterministic_fallback", fallback
