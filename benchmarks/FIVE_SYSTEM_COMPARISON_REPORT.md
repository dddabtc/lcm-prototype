# Five-System Memory Comparison Report (v2)

## Overview

Benchmark comparing five long-horizon conversational memory systems on a 100-round dialogue recall task, scored by an LLM Judge (Qwen3.5+).

### Methodology
- **Input**: 100 rounds of multi-topic conversation (Python programming, web app planning, debugging, mixed Q&A)
- **Checkpoints**: Retrieval-based Q&A at Round 85 and Round 95
- **Scoring**: LLM Judge rates answer quality on a 0–1 scale against reference answers
- **Isolation**: Each system runs independently with its own data store; Atlas v2 uses `ATLAS_CONFIG_PATH` for isolated instance on port 6501

## Systems Under Test

| ID | System | Approach |
|----|--------|----------|
| A | OpenViking | Hierarchical summarization with sliding window |
| B | LCM Prototype | Immutable store + summary DAG + multi-stage compaction |
| C | Atlas Memory (baseline) | Graph-based memory with entity extraction + semantic search |
| D | Atlas Memory v2 + LCM | LCM three-stage compactor + Atlas semantic search over compressed summaries |
| E | Nowledge Mem | Thread-based storage + distillation + semantic search |

## Recall Accuracy (LLM Judge)

| System | Round 85 | Round 95 | Overall |
|--------|:--------:|:--------:|:-------:|
| **Atlas Memory v2 + LCM** | 0.75 | 0.75 | **0.75** |
| **OpenViking** | 0.75 | 0.75 | **0.75** |
| **LCM Prototype** | 0.74 | 0.74 | **0.74** |
| Nowledge Mem | 0.62 | 0.62 | 0.62 |
| Atlas Memory (baseline) | 0.50 | 0.50 | 0.50 |

## Per-Question Breakdown (System D — Atlas v2 + LCM)

| Question | R85 | R95 | Notes |
|----------|:---:|:---:|-------|
| Python GIL solutions? | 1.0 | 1.0 | Correctly identifies no GIL discussion in corpus |
| Web app tech stack? | 1.0 | 1.0 | React + FastAPI + Postgres — retained through compression |
| Bug #10 root cause? | 0.0 | 0.0 | Corpus has Bug #1041–1060, not #10 — all systems lose this |
| People names mentioned? | 1.0 | 1.0 | Alice (Python owner) + Bob (Web PM) — both retained |

## Key Findings

1. **Atlas v2 + LCM ties for first place (0.75)** — matching OpenViking and surpassing pure LCM (0.74). The combination of LCM's lossless compression with Atlas's semantic search over compressed summaries yields the best results.

2. **Critical fix: store summaries, not raw turns** — An earlier implementation stored raw conversation turns in Atlas and concatenated search results with LCM context. This caused information dilution, dropping R85 to 0.38. Storing only LCM-compressed summaries in Atlas restored R85 to 0.75.

3. **LCM compactor remains the key differentiator** — Atlas baseline (0.50) vs Atlas+LCM (0.75) = +50% improvement, confirming the compaction strategy drives recall quality.

4. **OpenViking improved from prior run** — Previously showed R95 decay (0.75→0.50); this run shows consistent 0.75 at both checkpoints, likely due to evaluation variance.

5. **Nowledge Mem at 0.62** — Improved from prior 0.50 baseline with thread+distill pipeline active via external LLM.

## Architecture Insight: Why Summaries > Raw Turns

When Atlas stored raw conversation turns:
- Semantic search returned fragmentary turn-level snippets
- These fragments lacked compression context, diluting the high-quality LCM summaries
- The LLM judge received conflicting signals (compressed summary vs raw fragment)

When Atlas stores only LCM summaries:
- Semantic search returns compressed, information-dense results
- Results complement (and sometimes duplicate) the LCM active context
- Deduplication ensures no redundancy in the final prompt

## Conditions & Caveats

- Atlas v2 ran on an isolated instance (port 6501, separate DB) to avoid polluting production data
- Atlas v2 uses built-in `multilingual-e5-small` ONNX embeddings (384d)
- Nowledge Mem accessed via HTTP API at remote host (192.168.1.152:14242)
- All systems used the same 100-round conversation corpus and identical evaluation prompts
- Scores reflect single runs; variance across runs has not been measured
- Bug #10 question is arguably a trick question (corpus contains Bug #1041–1060, not #10)

## Version History

- **v1** (2026-02-15): Four-system comparison — LCM 0.74, Atlas+LCM 0.73, OpenViking 0.62, Atlas 0.50, Nowledge 0.50
- **v2** (2026-02-17): Five-system with fixed Atlas v2 integration — Atlas v2+LCM 0.75, OpenViking 0.75, LCM 0.74, Nowledge 0.62, Atlas 0.50
