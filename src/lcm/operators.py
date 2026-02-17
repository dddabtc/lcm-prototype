from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")
U = TypeVar("U")


def llm_map(items: Iterable[T], fn: Callable[[T], U]) -> list[U]:
    """Map-style operator intended for deterministic LLM transforms in prototype."""
    return [fn(x) for x in items]


def agentic_map(items: Iterable[T], fn: Callable[[T], U], *, stop_on_error: bool = False) -> list[U]:
    """Agentic mapping with optional fail-fast behavior."""
    out: list[U] = []
    for item in items:
        try:
            out.append(fn(item))
        except Exception:
            if stop_on_error:
                raise
    return out
