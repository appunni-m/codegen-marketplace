# Coverage MCP efficiency evidence

This document records a bounded, deterministic measurement of the current
schema-9 Coverage MCP projections. It is representative evidence from the
temporary fixture used by `mcp-evals`, not a performance promise for every
repository, report format, database size, or host.

## Reproduce the snapshot

Run the opt-in evaluator from the canonical Coverage MCP checkout:

```sh
make mcp-evals
```

The command writes `target/evals/mcp-eval-report.json`. The report is the
source of the values below; the table is a dated summary of the local snapshot
measured on 2026-08-22, not an independently maintained contract.

## Agent-facing projection results

The fixture contains two compatible LCOV snapshots, a changed source file, and
one uncovered changed region. The evaluator measured the following efficiency
properties:

| Measure | Result |
| --- | ---: |
| Bounded change workflow calls | `1` |
| Bounded change workflow bytes | `3,235` |
| Bounded change workflow source follow-ups | `0` |
| Compact change words | `510` |
| Exact audit words | `771` |
| Grouped region words | `120` |
| Exact line-audit words | `663` |
| Detailed history points | `2` |
| Bounded insight latency, p50/p95 | `5 / 6 ms` across 8 samples |

The compact representation is smaller because it emits each file path and
metric legend once, then uses grouped ranges and short status symbols. The
audit representation remains available when exact records are required. The
history projection keeps two detailed points and summarizes the remaining
window instead of returning every line record.

## Correctness and scope

The same run passed all 230 evaluator checks: usability 171, outcomes 14,
efficiency 16, protocol 9, safety 12, and reliability 8. Those checks cover
the public seven-tool inventory, response budgets, compact projections,
history shaping, source batching, managed-run polling, validation errors, and
shared transport behavior in the fixture.

These measurements do not prove production latency, universal token savings,
parser equivalence for every report format, or correctness of an arbitrary
external report. Raw LLVM/LCOV/other report inspection remains useful for a
narrow independent point-in-time check; Coverage MCP adds repository lineage,
freshness and artifact provenance, managed-run evidence, compatible history,
changed-code classification, source resolution, and bounded responses.
