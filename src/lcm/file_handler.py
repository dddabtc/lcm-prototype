from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass
class FileRecord:
    file_id: str
    path: str
    exploration_summary: str


class FileHandler:
    """Large-file registry with stable file IDs and exploration summaries."""

    def __init__(self):
        self._files: dict[str, FileRecord] = {}

    def register(self, path: str | Path, exploration_summary: str) -> FileRecord:
        p = Path(path)
        rec = FileRecord(file_id=str(uuid4()), path=str(p), exploration_summary=exploration_summary)
        self._files[rec.file_id] = rec
        return rec

    def get(self, file_id: str) -> FileRecord | None:
        return self._files.get(file_id)
