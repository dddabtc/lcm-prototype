# LoCoMo Benchmark Report

Standard evaluation using the [LoCoMo dataset](https://github.com/snap-research/locomo) (Snap Research, ACL 2024).

## Dataset

- **Source**: snap-research/locomo (10 long conversations, 1986 QA pairs)
- **Tested**: 3 conversations, 252 QA pairs (sampled, max 20 per category)
- **Categories**: single-hop (51), temporal (60), multi-hop (21), open-domain (60), adversarial (60)
- **Judge**: Qwen3.5+ via dashscope-intl (0.0-1.0 scoring)

## Systems

| ID | System | Approach |
|----|--------|----------|
| A | Atlas v2 | LCM compression + Atlas semantic search over summaries |
| B | LCM | Immutable store + summary DAG + multi-stage compaction |
| C | OpenViking | Hierarchical L1/L2 summarization with sliding window |
| D | Nowledge | Thread-based storage + LLM distillation + semantic search |
| E | Atlas baseline | Raw message chunks stored in Atlas + semantic search |

## Results

| System | Overall | single-hop | temporal | multi-hop | open-domain | adversarial |
|--------|:-------:|:----------:|:--------:|:---------:|:-----------:|:-----------:|
| **Atlas baseline** | **0.434** | 0.390 | 0.317 | 0.357 | **0.817** | 0.233 |
| Atlas v2 | 0.299 | 0.383 | 0.275 | 0.381 | 0.398 | 0.125 |
| OpenViking | 0.206 | 0.436 | 0.033 | 0.405 | 0.227 | 0.092 |
| LCM | 0.145 | 0.285 | 0.172 | 0.143 | 0.097 | 0.050 |
| Nowledge | 0.004 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 |

## Key Findings

1. **Atlas baseline wins on LoCoMo** — Pure semantic search over raw message chunks (0.434) outperforms all compression-based systems. This directly contradicts our earlier custom benchmark where compression-based systems dominated.

2. **Compression hurts on LoCoMo** — The ranking is inversely correlated with compression aggressiveness:
   - Atlas baseline (no compression): 0.434
   - Atlas v2 (LCM compression): 0.299
   - OpenViking (L1/L2 compression): 0.206
   - LCM (multi-stage compaction): 0.145

3. **Open-domain is the differentiator** — Atlas baseline scores 0.817 on open-domain questions, more than 2x the next system. These broad questions benefit from having raw details available for semantic retrieval, not compressed summaries.

4. **OpenViking's temporal weakness** — Scores only 0.033 on temporal questions. Its sliding window discards timestamps during L1/L2 compression, losing "when did X happen" information.

5. **Nowledge effectively non-functional** — Distillation did not produce searchable memories from the LoCoMo conversations. Likely an API integration issue rather than a fundamental limitation.

## Why Results Differ from Custom Benchmark

| Factor | Custom Benchmark | LoCoMo |
|--------|-----------------|--------|
| Conversations | 1 synthetic, 100 turns | 3 real, 270-695 turns each |
| Language | Chinese | English |
| Questions | 4, evaluated at 2 checkpoints | 252 across 5 categories |
| QA timing | Questions asked mid-conversation | Questions asked after full conversation |
| Content | Focused technical topics | Diverse personal conversations |

The custom benchmark asks questions **during** conversation (testing active memory management), while LoCoMo asks **after** the full conversation (testing retrieval over stored history). Compression helps with the former; raw storage + search helps with the latter.

## Implications

- **Compression is not universally beneficial** — It helps when context windows are the bottleneck (active conversation), but hurts when the task is retrieval over completed conversations.
- **The optimal strategy depends on the use case**:
  - Active conversation management → compression (LCM, OpenViking)
  - Post-conversation retrieval → semantic search over raw data (Atlas baseline)
  - Hybrid system needed for both scenarios
- **Atlas v2 should offer both modes** — compressed summaries for active context, raw storage for retrospective queries.

## Conditions

- Atlas v2 and Atlas baseline shared the same isolated instance (port 6501, separate DB)
- Atlas baseline stored messages in 5-turn chunks
- Nowledge accessed via HTTP API at remote host
- Single run per system; variance not measured
