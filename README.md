# LCM Prototype

A Python prototype implementing core ideas from **Lossless Context Management (LCM)** for long-horizon agent memory and context control.

## Paper Motivation (LCM)
LCM emphasizes preserving original information while enabling bounded-context operation via:
- Immutable raw record storage
- Hierarchical summaries with pointers back to originals
- Multi-stage compaction with deterministic fallback
- Active-context budgeting with soft/hard thresholds

## Architecture Overview
- **ImmutableStore (`store.py`)**: append-only JSONL message log with query APIs.
- **SummaryDAG (`dag.py`)**: hierarchical summary graph preserving pointers to source messages.
- **Compactor (`compactor.py`)**: normal / aggressive / deterministic compaction levels.
- **ContextManager (`context.py`)**: active window control via `tau_soft`, `tau_hard`.
- **LCMEngine (`engine.py`)**: orchestrates ingestion, storage, context update, and retrieval.
- **Supporting modules**:
  - `file_handler.py`: large file registration + exploration summaries
  - `operators.py`: `llm_map` / `agentic_map` style operators
  - `delegation.py`: anti-infinite-delegation guardrails

## Development
```bash
uv venv --python 3.14 .venv
uv pip install pytest tiktoken
pytest
```
