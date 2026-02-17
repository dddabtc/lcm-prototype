from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4


@dataclass(frozen=True)
class Message:
    id: str
    timestamp: str
    role: str
    content: str


class ImmutableStore:
    """Append-only message store backed by JSONL."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def append(self, role: str, content: str, *, message_id: str | None = None) -> Message:
        msg = Message(
            id=message_id or str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            role=role,
            content=content,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(msg), ensure_ascii=False) + "\n")
        return msg

    def _iter_all(self) -> Iterable[Message]:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield Message(**payload)

    def all(self) -> list[Message]:
        return list(self._iter_all())

    def get_by_id(self, message_id: str) -> Message | None:
        for msg in self._iter_all():
            if msg.id == message_id:
                return msg
        return None

    def get_by_ids(self, message_ids: list[str]) -> list[Message]:
        wanted = set(message_ids)
        result = [m for m in self._iter_all() if m.id in wanted]
        index = {m.id: m for m in result}
        return [index[mid] for mid in message_ids if mid in index]

    def query_time_range(self, start: datetime, end: datetime) -> list[Message]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start/end must be timezone-aware datetimes")
        out: list[Message] = []
        for msg in self._iter_all():
            ts = datetime.fromisoformat(msg.timestamp)
            if start <= ts <= end:
                out.append(msg)
        return out
