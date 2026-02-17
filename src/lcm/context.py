from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import List, Optional

from .compactor import Compactor
from .dag import SummaryDAG
from .store import Message


class ContextManager:
    """Maintains active context under soft/hard token budgets."""

    def __init__(
        self,
        *,
        compactor: Compactor,
        dag: SummaryDAG,
        tau_soft: int = 600,
        tau_hard: int = 1000,
        recent_window: int = 6,
    ):
        if tau_soft >= tau_hard:
            raise ValueError("tau_soft must be smaller than tau_hard")
        self.compactor = compactor
        self.dag = dag
        self.tau_soft = tau_soft
        self.tau_hard = tau_hard
        self.recent_window = recent_window

        self.recent_messages: List[Message] = []
        self.summary_node_ids: List[str] = []

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._soft_future: Optional[Future] = None

    def _total_tokens(self) -> int:
        recent_tokens = self.compactor.count_messages_tokens(self.recent_messages)
        summary_tokens = sum(self.dag.nodes[nid].token_count for nid in self.summary_node_ids if nid in self.dag.nodes)
        return recent_tokens + summary_tokens

    def _compress_recent_block(self, block: list[Message], target: int) -> str:
        _level, text = self.compactor.compress(block, target_tokens=target)
        return text

    def _flush_soft_future(self) -> None:
        if self._soft_future and self._soft_future.done():
            text, block = self._soft_future.result()
            node = self.dag.add_summary(block, text)
            self.summary_node_ids.append(node.id)
            self._soft_future = None

    def add_message(self, msg: Message) -> None:
        self._flush_soft_future()
        self.recent_messages.append(msg)

        total = self._total_tokens()
        if total > self.tau_hard:
            self._blocking_compress_until_within_hard()
            return

        if total > self.tau_soft and self._soft_future is None and len(self.recent_messages) > self.recent_window:
            block = self.recent_messages[:-self.recent_window]
            self.recent_messages = self.recent_messages[-self.recent_window:]
            self._soft_future = self._executor.submit(
                lambda b=block: (self._compress_recent_block(b, self.tau_soft // 2), b)
            )

    def _blocking_compress_until_within_hard(self) -> None:
        if self._soft_future is not None:
            text, block = self._soft_future.result()
            node = self.dag.add_summary(block, text)
            self.summary_node_ids.append(node.id)
            self._soft_future = None

        while self._total_tokens() > self.tau_hard and len(self.recent_messages) > 1:
            block_size = max(1, len(self.recent_messages) // 2)
            block = self.recent_messages[:block_size]
            self.recent_messages = self.recent_messages[block_size:]
            text = self._compress_recent_block(block, target=self.tau_soft // 2)
            node = self.dag.add_summary(block, text)
            self.summary_node_ids.append(node.id)

    def get_active_context(self) -> dict:
        self._flush_soft_future()
        summaries = [self.dag.nodes[nid] for nid in self.summary_node_ids if nid in self.dag.nodes]
        return {
            "recent_messages": self.recent_messages,
            "summaries": summaries,
            "token_estimate": self._total_tokens(),
        }
