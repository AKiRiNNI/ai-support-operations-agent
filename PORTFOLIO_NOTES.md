# Portfolio and Interview Notes

## What this project actually does

The project is a command-line customer-support operations agent. A ticket is sent to an OpenAI model together with three available function schemas. The model—not a Python routing table—chooses whether to search policy, inspect a booking, or create an escalation. Python executes each selected tool against local JSON data, returns the result to the model, and repeats until the model produces a structured customer response.

The project demonstrates four distinct ideas:

1. **LLM decision-making:** classify category and urgency from free-form text.
2. **Native function calling:** dynamically select and parameterize operational tools.
3. **Workflow execution:** use tool results to decide the next action, including escalation.
4. **Evaluation:** measure category, escalation, tool selection, runtime failure, and end-to-end behavior on a labeled benchmark.

## How to explain the loop in an interview

> I expose three JSON-schema functions to the model. The model returns a function call rather than a final answer when it needs data or an action. My Python loop validates and dispatches that call through a whitelist, sends the JSON result back using the call ID, and continues until there are no more tool calls. I then validate the model's structured result and log the tools used. The routing is model-driven, while execution and safety boundaries stay deterministic in Python.

## Evidence currently available

- 15-case v1 evaluation saved in `evaluation_results.json`
- 100% category accuracy on that small v1 set
- 100% escalation accuracy on that small v1 set
- 93.3% expected-tool recall on that small v1 set
- 60-case balanced baseline: 90.0% category accuracy, 93.3% escalation accuracy, 75.0% exact tool selection, 0% runtime failures
- Baseline analysis identified six category errors, four escalation errors, and fifteen tool-selection mismatches
- A v2 decision-boundary prompt is ready for a controlled before/after rerun on the same 60 cases

Do not present the 15-case results as production performance. The set is synthetic and small.

## Honest resume bullets now

- **AI Workflow Automation:** Built a Python support-operations agent using OpenAI native function calling to classify ticket category and urgency, dynamically route requests across knowledge retrieval, booking lookup, and escalation tools, and generate structured customer responses.
- **Testing & Validation:** Evaluated 60 labeled synthetic support cases across five operational categories, achieving 90% category accuracy, 93% escalation accuracy, and 0% runtime failures; analyzed six classification errors, four escalation errors, and fifteen tool-routing mismatches to refine decision boundaries.

## Resume bullet after running the 60-case benchmark

Replace brackets only with measured values from `results/benchmark_60.json`:

- Evaluated 60 labeled synthetic support cases across five operational categories, achieving **[X%] category accuracy**, **[Y%] escalation accuracy**, and **[Z%] exact tool-selection accuracy**.

Only claim an improvement percentage after two comparable benchmark runs using the same dataset and model configuration.
