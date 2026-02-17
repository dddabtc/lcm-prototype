# LCM Prototype Test Report

## 1) E2E 测试结果

执行命令：

```bash
cd /home/ubuntu/lcm-prototype
source .venv/bin/activate
uv run pytest -v
```

结果：**11 passed**（包含新增 `tests/test_e2e.py`）。

新增 e2e 覆盖内容：
- 50 轮对话（每轮 200~500 tokens）
- 参数：`tau_soft=4000`, `tau_hard=6000`
- 验证点：
  1. 所有消息都写入 immutable store
  2. DAG 有摘要层，且可构建层级父节点
  3. active context 稳态保持 `< tau_hard`
  4. 通过 `dag.expand(node_id)` 可回溯原始 message ids
  5. normal / aggressive / deterministic fallback 三种压缩路径都触发

## 2) 性能基准

脚本：`benchmarks/bench_context.py`

执行（为避免外部网络波动，关闭 LLM，测框架本体性能）：

```bash
source .venv/bin/activate
LCM_DISABLE_LLM=1 uv run python benchmarks/bench_context.py
```

结果：

| 消息数 | 平均添加延迟(ms) | P95(ms) | 压缩耗时估计(ms) | 内存峰值(MB) | DAG 深度 |
|---:|---:|---:|---:|---:|---:|
| 100 | 1.477 | 2.532 | 1.387 | 0.256 | 1 |
| 500 | 1.225 | 2.353 | 6.046 | 0.367 | 3 |
| 1000 | 1.078 | 2.196 | 12.472 | 0.895 | 16 |

说明：
- 当前原型在本机负载下，添加消息延迟保持在毫秒级。
- 消息规模增大时，DAG 深度明显上升，说明层级压缩在起作用。

## 3) LLM 压缩质量（样例）

模型与接口：
- Model: `gemini-2.5-flash`
- Base: `https://generativelanguage.googleapis.com/v1beta/openai`
- OpenAI-compatible `/chat/completions`

### 示例 A（normal）
原文（节选）：
> The system must preserve all facts decisions constraints and open tasks while compacting context for long multi-turn dialogues in a hierarchical summary DAG architecture... (重复长段)

压缩后：
> [NORMAL] The system's core requirement is to compact context for long multi-turn dialogues. This compaction must utilize a hierarchical summary DAG architecture and strictly preserve all facts, decisions, constraints, and open tasks.

### 示例 B（aggressive）
原文：同上（长文本）

压缩后：
> [AGGRESSIVE] System must preserve all facts, decisions, constraints, and open tasks when compacting context for long multi-turn dialogues using a hierarchical summary DAG architecture.

观察：
- normal 版本更完整，适合作为中等压缩层。
- aggressive 更短，适合接近硬阈值时快速收敛。

## 4) 与论文式理想描述的差距

1. **token 计数仍为简化估计**（按空格分词），与真实 tokenizer 有偏差。
2. **层级策略较启发式**（按块切分+节点合并），尚非最优调度。
3. **异步压缩队列较简单**（单线程 future），未做优先级与批处理。
4. **压缩质量评估缺少自动指标**（如 factual consistency / ROUGE / recall@facts）。
5. **持久化仅覆盖 DAG**，ContextManager 的运行态（pending future 等）未序列化。

## 5) 下一步改进建议

1. 接入真实 tokenizer（如 tiktoken 或模型原生 token 统计）替换粗略估计。
2. 增加“事实单元”回归测试：压缩前后关键事实、数字、约束必须保留。
3. 为 DAG 引入可控重平衡策略，限制深度过快增长。
4. 增加压缩缓存（相同输入哈希命中）降低重复调用成本。
5. 完善会话恢复：除 DAG 外持久化 ContextManager 状态。
6. 基准拆分为两组：`LLM on`（端到端真实质量/时延）与 `LLM off`（框架纯性能）。
