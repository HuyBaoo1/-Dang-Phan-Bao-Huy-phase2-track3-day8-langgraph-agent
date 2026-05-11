# Day 08 Lab Report

- Name:Dang Phan Bao Huy
- Repo/commit:
- Date:11/5/2026

## 1. Architecture

This LangGraph workflow is built with explicit node boundaries and conditional routing. The graph uses:

- `intake` → normalize the query and collect audit metadata.
- `classify` → choose `simple`, `tool`, `missing_info`, `risky`, or `error` routes using keyword heuristics.
- `tool` / `evaluate` → mock tool execution followed by a retry gate based on `evaluation_result`.
- `retry` → bounded retry logic with `max_attempts`; if exhausted, the workflow goes to `dead_letter`.
- `risky_action` → proposed action + `approval` before tool execution.
- `clarify` / `answer` / `finalize` → safe termination for all routes.

## 2. State schema

Important fields:

| Field | Reducer | Why |
|---|---|---|
| messages | append | audit trail of agent events |
| tool_results | append | preserves all tool call outputs for replay and debugging |
| errors | append | captures retry and failure history |
| events | append | records node-level transitions and diagnostics |
| route | overwrite | current route choice for the scenario |
| evaluation_result | overwrite | retry gate state used by `route_after_evaluate` |
| attempt | overwrite | current retry attempt counter |

## 3. Scenario results

- Total scenarios: 7
- Success rate: 100.00%
- Average nodes visited: 6.43
- Total retries: 3
- Total dead letters: 1
- Total interrupts: 2

| Scenario | Expected route | Actual route | Success | Retries | Interrupts | Dead letters |
|---|---|---|---:|---:|---:|---:|
| S01_simple | simple | simple | True | 0 | 0 | 0 |
| S02_tool | tool | tool | True | 0 | 0 | 0 |
| S03_missing | missing_info | missing_info | True | 0 | 0 | 0 |
| S04_risky | risky | risky | True | 0 | 1 | 0 |
| S05_error | error | error | True | 2 | 0 | 0 |
| S06_delete | risky | risky | True | 0 | 1 | 0 |
| S07_dead_letter | error | error | True | 1 | 0 | 1 |

## 4. Failure analysis

1. Retry or tool failure:
   - The `error` route uses a bounded retry loop and evaluates tool output with `evaluation_result`.
   - If `attempt >= max_attempts`, the graph transitions to `dead_letter` to prevent infinite loops.

2. Risky action without approval:
   - `risky` scenarios go through `risky_action` then `approval` before the tool.
   - If approval were rejected, the graph would safely divert to `clarify`.

## 5. Persistence / recovery evidence

The CLI supports a checkpointer adapter in `persistence.py`.
- `memory` is the default in `configs/lab.yaml`.
- `sqlite` can be enabled via `checkpointer: sqlite` and a valid `database_url`.
- The graph uses `thread_id` per run to keep state scoped to each scenario.

## 6. Extension work

- Added `dead_letter_count` to metrics for explicit failure visibility.
- Implemented optional SQLite checkpointer wiring in `persistence.py`.

## 7. Improvement plan

If I had one more day, I would productionize this graph by:

- adding real HITL interrupt UI and approval workflow tracking,
- persisting state history for crash recovery and time-travel replay,
- instrumenting response latency and operational tracing.
