from __future__ import annotations


class DelegationGuard:
    """Simple anti-infinite-delegation mechanism."""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def allow(self, depth: int) -> bool:
        return depth < self.max_depth

    def ensure(self, depth: int) -> None:
        if not self.allow(depth):
            raise RuntimeError(f"Delegation depth exceeded: {depth} >= {self.max_depth}")
