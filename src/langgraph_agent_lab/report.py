"""Report generation helper."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def render_report_stub(metrics: MetricsReport) -> str:
    """Return a richer report based on metrics."""
    rows = []
    for item in metrics.scenario_metrics:
        rows.append(
            f"| {item.scenario_id} | {item.expected_route} | {item.actual_route or 'unknown'} | {item.success} | {item.retry_count} | {item.interrupt_count} | {item.dead_letter_count} |"
        )

    rows_text = "\n".join(rows)
    return f"""# Day 08 Lab Report

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

- Total scenarios: {metrics.total_scenarios}
- Success rate: {metrics.success_rate:.2%}
- Average nodes visited: {metrics.avg_nodes_visited:.2f}
- Total retries: {metrics.total_retries}
- Total dead letters: {metrics.total_dead_letters}
- Total interrupts: {metrics.total_interrupts}

| Scenario | Expected route | Actual route | Success | Retries | Interrupts | Dead letters |
|---|---|---|---:|---:|---:|---:|
{rows_text}

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
"""


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report_stub(metrics), encoding="utf-8")
