from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict
from uuid import uuid4

from .store import Message


@dataclass
class SummaryNode:
    id: str
    content: str
    children_ids: list[str] = field(default_factory=list)
    level: int = 1
    token_count: int = 0


class SummaryDAG:
    """Hierarchical summary graph with pointers to original messages."""

    def __init__(self):
        self.nodes: Dict[str, SummaryNode] = {}
        self.node_to_message_ids: Dict[str, list[str]] = {}

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text.split())) if text.strip() else 0

    def add_summary(self, messages: list[Message], summary_text: str, *, child_node_ids: list[str] | None = None) -> SummaryNode:
        child_node_ids = child_node_ids or []
        if child_node_ids:
            level = max(self.nodes[c].level for c in child_node_ids) + 1
            message_ids: list[str] = []
            for cid in child_node_ids:
                message_ids.extend(self.node_to_message_ids.get(cid, []))
        else:
            level = 1
            message_ids = [m.id for m in messages]

        node = SummaryNode(
            id=str(uuid4()),
            content=summary_text,
            children_ids=list(child_node_ids),
            level=level,
            token_count=self._estimate_tokens(summary_text),
        )
        self.nodes[node.id] = node
        self.node_to_message_ids[node.id] = list(dict.fromkeys(message_ids))
        return node

    def expand(self, node_id: str) -> list[str]:
        if node_id not in self.nodes:
            raise KeyError(f"Unknown node_id: {node_id}")
        return list(self.node_to_message_ids.get(node_id, []))

    def get_at_level(self, level: int) -> list[SummaryNode]:
        return [n for n in self.nodes.values() if n.level == level]

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "node_to_message_ids": self.node_to_message_ids,
        }
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SummaryDAG":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        dag = cls()
        for raw in data.get("nodes", []):
            node = SummaryNode(**raw)
            dag.nodes[node.id] = node
        dag.node_to_message_ids = {
            node_id: list(msg_ids) for node_id, msg_ids in data.get("node_to_message_ids", {}).items()
        }
        return dag
