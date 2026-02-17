# FOUR SYSTEM COMPARISON REPORT (Qwen3.5+)

## Scope
- 100轮对话，Round 85/95 检索问答，LLM Judge 评分。
- System D 为新增 Nowledge Mem 适配器（thread append + distill，失败回退 create memory）。

## API 验证（Nowledge Mem @192.168.1.113:14242）
- `GET /health`: 正常（测试初期可用）。
- `POST /threads`, `POST /threads/{id}/append`, `POST /memories`: 可用。
- `POST /memories/distill`: 返回失败（No memories could be distilled / failed after retries）。
- `POST /memories/search`: 可调用但返回空结果（即使已写入 memories）。
- 测试末期服务出现连接拒绝（`Connection refused`），影响继续复测。

## 压缩效率

| 系统 | 压缩事件数 | 平均压缩比(after/before) | 平均耗时(s) |
|---|---:|---:|---:|
| System A - OpenViking | 6 | 0.070 | 15.09 |
| System B - LCM Prototype | 4 | 0.837 | 21.62 |
| System C - Atlas Memory | 2 | 0.106 | 28.41 |
| System D - Nowledge Mem | 5 | 0.069 | 0.07 |

## 记忆保留 / 召回（LLM Judge）

| 系统 | Round85 | Round95 | Overall |
|---|---:|---:|---:|
| System B - LCM Prototype | 0.74 | 0.74 | 0.74 |
| System A - OpenViking | 0.75 | 0.50 | 0.62 |
| System C - Atlas Memory | 0.50 | 0.50 | 0.50 |
| System D - Nowledge Mem | 0.00 | 0.00 | 0.00 |

## 结论
- 排名：System B - LCM Prototype > System A - OpenViking > System C - Atlas Memory > System D - Nowledge Mem
- LCM Prototype 仍为最佳（0.74），OpenViking 次之（0.62），Atlas 为 0.50。
- Nowledge Mem 本次为 0.00：核心瓶颈是 distill 不可用、search 空结果，导致 recall 阶段拿不到有效上下文。
- 建议先在 Nowledge 侧完成 LLM provider 配置并验证 distill/search 正常，再复跑 100 轮。
