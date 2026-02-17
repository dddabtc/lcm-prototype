from __future__ import annotations

from pathlib import Path

from .compactor import Compactor
from .context import ContextManager
from .dag import SummaryDAG
from .store import ImmutableStore, Message


class LCMEngine:
    """Main loop: ingest message -> store -> context management -> active context."""

    def __init__(self, store_path: str | Path, *, tau_soft: int = 600, tau_hard: int = 1000):
        self.store = ImmutableStore(store_path)
        self.dag = SummaryDAG()
        self.compactor = Compactor()
        self.context = ContextManager(
            compactor=self.compactor,
            dag=self.dag,
            tau_soft=tau_soft,
            tau_hard=tau_hard,
        )

    def receive(self, role: str, content: str) -> dict:
        msg = self.store.append(role=role, content=content)
        self.context.add_message(msg)
        return self.context.get_active_context()

    def bootstrap_from_store(self) -> None:
        for msg in self.store.all():
            self.context.add_message(msg)

    def get_message(self, message_id: str) -> Message | None:
        return self.store.get_by_id(message_id)
