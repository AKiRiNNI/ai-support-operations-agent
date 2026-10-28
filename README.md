# AI Support Operations Agent

一个小而真实的客服运营 Agent 作品集项目。它使用 OpenAI Responses API 的原生函数调用，让模型动态决定是否查询知识库、读取预订信息或创建人工升级；代码没有使用 LangChain 或 LangGraph。

> 技术栈说明：本项目使用 **OpenAI**，不是 Claude/Anthropic。

## 项目能力

- 理解工单并判断类别、紧急程度
- 由模型按上下文动态选择工具，而不是 Python `if/else` 硬编码路由
- 把工具结果返回给模型，支持连续多轮工具调用
- 输出结构化内部结果并生成面向客户的答复
- 将升级记录持久化到本地 JSON
- 记录每张工单实际调用的工具
- 使用 60 条平衡合成工单评估类别、升级、工具选择和端到端可靠性
- 使用 60 条 ABCD/MultiWOZ 公开数据 holdout 测试跨数据源分类泛化

数据来源、标签规则和评估限制详见 [`BENCHMARK_METHODOLOGY.md`](BENCHMARK_METHODOLOGY.md) 和 [`EXTERNAL_DATA_METHODOLOGY.md`](EXTERNAL_DATA_METHODOLOGY.md)。

## 一分钟理解这个项目

这不是普通的关键词分类脚本。Python 只负责提供安全的工具和执行边界，模型负责根据工单动态决定下一步：

1. 客户提交自然语言工单。
2. 模型判断类别和紧急程度。
3. 模型选择是否调用知识库、预订查询或人工升级。
4. Python 执行工具，并把真实 JSON 结果返回模型。
5. 模型可继续调用其他工具，或输出最终客户回复。
6. 应用验证结构化结果并记录实际工具调用。

## 一个月后如何重新启动

```bash
cd ai-support-operations-agent
source .venv/bin/activate
export OPENAI_API_KEY="your_api_key_here"
python app.py --ticket-id T-200 --message "My coach for BK-1003 was cancelled and I am stranded."
```

如果 `.venv` 不存在，再执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 架构

```text
CLI ticket
   │
   ▼
SupportAgent ──► OpenAI Responses API
   ▲                    │
   │                    ▼ dynamic function call
   └── function output ─ tools.py ──► local JSON data
                        │
                        └──► final structured result
```

核心循环在 `agent.py`：把工单和工具定义发给模型；若返回 `function_call`，执行白名单中的本地函数，再以 `function_call_output` 回传。没有工具调用时，解析模型最终 JSON。循环设置了最大轮数，避免失控。

```text
模型: lookup_booking({"booking_id":"BK-1003"})
应用: {"ok":true,"booking":{"status":"disrupted", ...}}
模型: create_escalation({"ticket_id":"T-002", ...})
应用: {"ok":true,"escalation":{"escalation_id":"ESC-0001", ...}}
模型: 最终分类、紧急度和客户答复
```

## 项目结构

```text
ai-support-operations-agent/
├── app.py
├── agent.py
├── tools.py
├── evaluate.py
├── evaluate_external.py
├── scripts/
│   └── build_external_holdout.py
├── data/
│   ├── bookings.json
│   ├── knowledge_base.json
│   ├── escalations.json
│   └── external/licenses/
├── tests/
│   ├── benchmark_cases.json
│   ├── external_holdout_cases.json
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_cases.json
├── requirements.txt
├── .env.example
└── .gitignore
```

## 安装与运行

需要 Python 3.10+。API key 只通过环境变量传入，不写进源码。

```bash
cd ai-support-operations-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key_here"
# 可选：export OPENAI_MODEL="gpt-5.4-mini"
python app.py --ticket-id T-100 --message "My coach for BK-1003 was cancelled and I am stranded."
```

输出示例：

```json
{
  "ticket_id": "T-100",
  "category": "service disruption",
  "urgency": "high",
  "tools_used": ["lookup_booking", "create_escalation"],
  "escalation_status": "created",
  "final_response": "I’m sorry your service was disrupted. I’ve escalated this to our operations team for urgent help."
}
```

## 测试与评估

不需要 API key 的单元测试和确定性端到端演示：

```bash
python -m unittest discover -s tests -v
```

原始 v1 评估结果保存在 `evaluation_results.json`，包含 15 条合成工单：类别准确率 100%、升级准确率 100%、期望工具召回率 93.3%。这个集合较小，因此只作为早期验证结果。

当前 benchmark 是 `tests/benchmark_cases.json`：共 60 条，五类工单各 12 条，其中 19 条预期升级。v1 baseline 已完整运行，结果保存在 `results/benchmark_60.json`：

- 60/60 成功完成，运行失败率 0%
- 类别准确率 90.0%
- 升级准确率 93.3%
- 工具完全匹配率 75.0%，工具 F1 92.9%
- 端到端通过率 65.0%

根据 baseline 暴露的分类边界、漏升级和多余知识库查询问题，prompt 已升级为 `v2-decision-boundaries`。使用完全相同的数据集运行 v2，并保留独立结果：

```bash
python evaluate.py \
  --cases tests/benchmark_cases.json \
  --output results/benchmark_60_v2.json

# 快速试跑前三条（会产生 API 费用）
python evaluate.py \
  --cases tests/benchmark_cases.json \
  --limit 3 \
  --output results/smoke_3.json
```

评估使用临时 escalation 文件，不会污染 `data/escalations.json`。运行进度会显示在终端，完整 JSON 会写入 `--output` 指定的文件。

v2 结果：类别准确率 93.3%、升级准确率 98.3%、工具完全匹配率 81.7%、端到端通过率 75.0%。工具 F1 从 92.9% 降至 87.9%，说明新版虽然改善了主要决策和完全匹配，也在少数 policy 案例中漏掉知识库调用。由于 v2 是根据同一组 60 条 baseline 错误调优的，这组数据现在属于 development benchmark；独立泛化能力仍需要新的 holdout set 验证。

报告包含：

- `category_accuracy`：类别完全匹配率
- `escalation_accuracy`：是否成功创建升级的匹配率
- `tool_exact_match_rate`：实际工具集合与期望工具集合完全一致的比例
- `tool_precision` / `tool_recall` / `tool_f1`：工具选择质量
- `runtime_failure_rate`：API、解析或工具执行失败比例
- `end_to_end_pass_rate`：分类、升级和工具完全匹配同时正确的比例
- `by_category`：五类工单的分组结果

工具调用具有非确定性，因此工具指标是诊断信号，不应被视为唯一正确路径。评估中的升级案例使用临时文件，不会修改演示数据。

### 公开数据 external holdout

为了避免只在自己写的测试题上调 prompt，项目还包含 60 条来自 ABCD v1.1 和 MultiWOZ 2.2 官方 test split 的外部案例：`booking issue`、`refund/payment`、`general information` 各 20 条。生成过程固定上游 commit、验证 SHA-256，并保留每条记录的 source ID、原标签、许可证和转换说明。

```bash
# 首次运行需要网络；原始文件只缓存在 .cache/，不会提交 GitHub
python scripts/build_external_holdout.py

# 先跑 3 条确认 API 配置，再跑完整 60 条
python evaluate_external.py --limit 3 --output results/external_holdout_smoke_3.json
python evaluate_external.py --output results/external_holdout_v1.json
```

外部数据只评分 category accuracy。工具和升级行为会记录下来用于审计，但不会伪装成有上游 ground truth 的准确率。这个数据集没有用于 fine-tuning，也不应该在查看结果后继续用于 prompt 调优。

首次完整 external baseline 已保存到 `results/external_holdout_v1.json`：60/60 成功完成，runtime failure 为 0%，整体 category accuracy 为 61.7%。分数据源结果为 ABCD 87.5%、MultiWOZ 10.0%。错误分析发现，新建预订和既有 booking issue 的边界不明确，导致 18/20 个 MultiWOZ 请求落入 `general information`；另外 5 个退款、退货政策或信用卡失败案例也落入兜底类别。详见 [`results/EXTERNAL_HOLDOUT_ANALYSIS.md`](results/EXTERNAL_HOLDOUT_ANALYSIS.md)。

因为这组结果已经被查看，它现在是 external diagnostic baseline，不再是未来 prompt 修改的盲测集。下一次泛化验证需要使用不同 ABCD records 和尚未使用的第二个 MultiWOZ test 文件。

根据 external v1 的错误分析，prompt 已升级为 `v3-external-boundaries`：新建火车、出租车、shuttle 或 coach 预订属于 `booking issue`；酒店、餐厅和景点等不支持领域仍属于 `general information`；退货/退款政策、发起退款、信用卡被拒和支付失败统一属于 `refund/payment`。在相同60条上重跑只用于 before/after development comparison，不应描述为新的独立 holdout：

```bash
python evaluate_external.py \
  --output results/external_development_v3.json
```

不要覆盖 `results/external_holdout_v1.json`。v3 的最终泛化结论仍需第二组未使用的外部数据验证。

v3 在相同60条上的 controlled development rerun 已完成：category accuracy 从61.7%提升到90.0%，ABCD 从87.5%提升到97.5%，MultiWOZ 从10.0%提升到75.0%。17个原错误案例得到修正；剩余问题包括4个已知 ontology mismatch、1个退款分类错误和1个无效最终 JSON。Agent 现在会对无效最终 JSON 自动发起一次格式纠正重试。

可以只验证曾经失败的 train-booking case，而不再支付完整60条的调用费用：

```bash
python evaluate_external.py \
  --ticket-id EXT-MWOZ-MUL0432 \
  --output results/final_json_retry_smoke.json
```

## 限制

- JSON 文件写入没有数据库锁，不适合并发生产流量。
- 知识库搜索仅使用关键词重叠，不是语义检索。
- 最终 JSON 通过应用层校验；当前未使用 Responses API 的结构化输出 schema。
- 外部 benchmark 是研究数据而非生产客服日志，目前只覆盖五个类别中的三个，并存在跨领域 ontology mapping 限制。
- 尚未覆盖真实生产语言分布、提示注入、多语言和复杂退款政策。
- Agent 能创建升级，但不能修改预订或发起退款。

## 后续改进

- 增加结构化输出 schema、重试和更细的可观测性
- 用 SQLite 替代可变 JSON，并为升级操作加入幂等键
- 扩充人工标注评估集，记录延迟、成本和客户答复质量
- 加入提示注入和工具故障测试
- 核心 CLI 稳定后再添加 Streamlit UI

函数调用实现遵循 [OpenAI 官方 Function Calling 指南](https://developers.openai.com/api/docs/guides/function-calling) 中的 Responses API 多步工具调用流程。
