# LCM Prototype

A Python prototype implementing core ideas from **Lossless Context Management (LCM)** for long-horizon agent memory and context control.

## Original Paper

📄 **LCM: Lossless Context Management**
- Author: Clint Ehrlich, Voltropy PBC
- Date: 2026-02-14
- PDF: [`docs/LCM-paper-voltropy-2026.pdf`](docs/LCM-paper-voltropy-2026.pdf)
- Source: https://papers.voltropy.com/LCM

### Key Ideas
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

## Benchmark: Memory System Comparison

Five system configurations tested on 100-round conversational recall (Qwen3.5+ as LLM Judge):

| System | Round 85 | Round 95 | Overall |
|--------|----------|----------|---------|
| Atlas v2 | 0.75 | 0.75 | **0.75** |
| OpenViking | 0.75 | 0.75 | **0.75** |
| LCM Prototype | 0.74 | 0.74 | **0.74** |
| Nowledge Mem | 0.62 | 0.62 | 0.62 |
| Atlas Memory (baseline) | 0.50 | 0.50 | 0.50 |

**Key finding**: Atlas v2 stores only compressed summaries (not raw turns) via semantic search, achieving 0.75 overall — a +50% boost over baseline Atlas (0.50) and matching OpenViking. The LCM three-stage compactor remains the primary differentiator.

→ [Detailed Report](benchmarks/FIVE_SYSTEM_COMPARISON_REPORT.md)
