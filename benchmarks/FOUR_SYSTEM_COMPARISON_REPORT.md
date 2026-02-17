# Four-System Memory Comparison Report

## Overview

Benchmark comparing four long-horizon conversational memory systems on a 100-round dialogue recall task, scored by an LLM Judge (Qwen3.5+).

### Methodology
- **Input**: 100 rounds of multi-topic conversation (Python programming, web app planning, debugging, mixed Q&A)
- **Checkpoints**: Retrieval-based Q&A at Round 85 and Round 95
- **Scoring**: LLM Judge rates answer quality on a 0–1 scale against reference answers
- **Compression**: Each system compresses conversation history using its own strategy; compression ratio and latency are recorded

## Systems Under Test

| ID | System | Approach |
|----|--------|----------|
| A | OpenViking | Hierarchical summarization with sliding window |
| B | LCM Prototype | Immutable store + summary DAG + multi-stage compaction |
| C | Atlas Memory | Graph-based memory with entity extraction |
| D | Nowledge Mem | Thread-based storage + distillation + semantic search |

## Compression Efficiency

| System | Events | Avg Ratio (after/before) | Avg Latency (s) |
|--------|-------:|-------------------------:|-----------------:|
| OpenViking | 6 | 0.070 | 15.09 |
| LCM Prototype | 4 | 0.837 | 21.62 |
| Atlas Memory | 2 | 0.106 | 28.41 |
| Nowledge Mem | 5 | 0.069 | 0.07 |

**Notes:**
- LCM Prototype preserves more tokens by design (lossless philosophy), resulting in a higher ratio.
- Nowledge Mem's low latency reflects its fallback path: external LLM compression → direct memory creation via API, bypassing the built-in distillation pipeline.

## Recall Accuracy (LLM Judge)

| System | Round 85 | Round 95 | Overall |
|--------|:--------:|:--------:|:-------:|
| **LCM Prototype** | 0.74 | 0.74 | **0.74** |
| OpenViking | 0.75 | 0.50 | 0.62 |
| Atlas Memory | 0.50 | 0.50 | 0.50 |
| Nowledge Mem | 0.50 | 0.50 | 0.50 |

## Key Findings

1. **LCM Prototype leads overall (0.74)** — consistent recall at both checkpoints, benefiting from its lossless storage and hierarchical summary structure.

2. **OpenViking shows early strength but decays** — scores 0.75 at Round 85 but drops to 0.50 at Round 95, suggesting its sliding window loses older context.

3. **Atlas Memory and Nowledge Mem tie at 0.50** — both provide adequate but not exceptional recall across checkpoints.

4. **Nowledge Mem operated in degraded mode** — its native distillation pipeline was unavailable (requires LLM provider configuration). Scores were achieved using an external compression fallback + semantic search. With full distillation enabled, performance may improve.

## Conditions & Caveats

- Nowledge Mem's distillation endpoint (`/memories/distill`) requires a configured LLM provider. During this benchmark, distillation consistently failed; memories were created via external Qwen3.5+ compression as a fallback.
- Embedding model and semantic search were verified operational before scoring.
- All systems used the same 100-round conversation corpus and identical evaluation prompts.
- Scores reflect a single run; variance across runs has not been measured.
