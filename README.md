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
├── data/
│   ├── bookings.json
│   ├── knowledge_base.json
│   └── escalations.json
├── tests/
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

当前 benchmark 是 `tests/benchmark_cases.json`：共 60 条，五类工单各 12 条，其中 19 条预期升级。运行真实模型评估并自动保存结果：

```bash
python evaluate.py \
  --cases tests/benchmark_cases.json \
  --output results/benchmark_60.json

# 快速试跑前三条（会产生 API 费用）
python evaluate.py \
  --cases tests/benchmark_cases.json \
  --limit 3 \
  --output results/smoke_3.json
```

评估使用临时 escalation 文件，不会污染 `data/escalations.json`。运行进度会显示在终端，完整 JSON 会写入 `--output` 指定的文件。

报告包含：

- `category_accuracy`：类别完全匹配率
- `escalation_accuracy`：是否成功创建升级的匹配率
- `tool_exact_match_rate`：实际工具集合与期望工具集合完全一致的比例
- `tool_precision` / `tool_recall` / `tool_f1`：工具选择质量
- `runtime_failure_rate`：API、解析或工具执行失败比例
- `end_to_end_pass_rate`：分类、升级和工具完全匹配同时正确的比例
- `by_category`：五类工单的分组结果

工具调用具有非确定性，因此工具指标是诊断信号，不应被视为唯一正确路径。评估中的升级案例使用临时文件，不会修改演示数据。

## 限制

- JSON 文件写入没有数据库锁，不适合并发生产流量。
- 知识库搜索仅使用关键词重叠，不是语义检索。
- 最终 JSON 通过应用层校验；当前未使用 Responses API 的结构化输出 schema。
- 评估集是合成数据，尚未覆盖真实客户语言分布、提示注入、多语言和复杂退款政策。
- Agent 能创建升级，但不能修改预订或发起退款。

## 后续改进

- 增加结构化输出 schema、重试和更细的可观测性
- 用 SQLite 替代可变 JSON，并为升级操作加入幂等键
- 扩充人工标注评估集，记录延迟、成本和客户答复质量
- 加入提示注入和工具故障测试
- 核心 CLI 稳定后再添加 Streamlit UI

函数调用实现遵循 [OpenAI 官方 Function Calling 指南](https://developers.openai.com/api/docs/guides/function-calling) 中的 Responses API 多步工具调用流程。
