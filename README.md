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

## Benchmarks

### Custom Benchmark (100-round conversational recall)

Questions asked mid-conversation at Round 85 and 95. Qwen3.5+ as LLM Judge.

| System | Round 85 | Round 95 | Overall |
|--------|----------|----------|---------|
| Atlas v2 | 0.75 | 0.75 | **0.75** |
| OpenViking | 0.75 | 0.75 | **0.75** |
| LCM Prototype | 0.74 | 0.74 | **0.74** |
| Nowledge Mem | 0.62 | 0.62 | 0.62 |
| Atlas baseline | 0.50 | 0.50 | 0.50 |

→ [Detailed Report](benchmarks/FIVE_SYSTEM_COMPARISON_REPORT.md)

### LoCoMo Standard Benchmark (snap-research/locomo, ACL 2024)

Questions asked after full conversation (retrieval over stored history). 3 conversations, 252 QA pairs.

| System | Overall | single-hop | temporal | multi-hop | open-domain | adversarial |
|--------|:-------:|:----------:|:--------:|:---------:|:-----------:|:-----------:|
| Atlas baseline | **0.434** | 0.390 | 0.317 | 0.357 | **0.817** | 0.233 |
| Atlas v2 | 0.299 | 0.383 | 0.275 | 0.381 | 0.398 | 0.125 |
| OpenViking | 0.206 | 0.436 | 0.033 | 0.405 | 0.227 | 0.092 |
| LCM | 0.145 | 0.285 | 0.172 | 0.143 | 0.097 | 0.050 |
| Nowledge | 0.004 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 |

→ [Detailed Report](benchmarks/LOCOMO_BENCHMARK_REPORT.md)

### Key Insight

Compression dominates during active conversation (custom benchmark), but raw semantic search wins for post-conversation retrieval (LoCoMo). The optimal memory system needs both modes.
