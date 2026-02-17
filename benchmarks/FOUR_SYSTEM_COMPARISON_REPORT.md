# FOUR SYSTEM COMPARISON REPORT (Qwen3.5+)

## Scope
- 100轮对话，Round 85/95 检索问答，LLM Judge 评分。
- System D 为新增 Nowledge Mem 适配器（thread append + distill，失败回退 create memory）。

## API 验证（Nowledge Mem @192.168.1.113:14242）
- `GET /health`: 正常。
- embedding 已安装完成，`POST /memories/search` 检索可用，能稳定返回历史 benchmark memories。
- `POST /threads`, `POST /threads/{id}/append`, `POST /memories`: 可用。
- `POST /memories/distill`: 仍依赖外部 LLM 配置；当前环境下仍可能出现 distill 失败，需要单独配置/校验 provider。

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
| System D - Nowledge Mem | 0.50 | 0.50 | 0.50 |

## 结论
- 排名：System B - LCM Prototype (0.74) > System A - OpenViking (0.62) > System C - Atlas Memory (0.50) = System D - Nowledge Mem (0.50)。
- 复评分后，Nowledge Mem 从 0.00 提升到 0.50，说明此前低分主要由 search 未就绪导致，而非 memory 数据本身缺失。
- 当前 Nowledge 的关键状态：search 已可用（embedding 正常），但 distill 仍需稳定的 LLM provider 才能持续工作。
- 若补齐 distill 的 provider 配置并重新跑全量 100 轮，Nowledge 仍有继续提升空间。
