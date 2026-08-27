# Coverage campaign packet contracts

Use these compact JSON-shaped contracts for model handoffs. Preserve exact IDs
from Coverage MCP and repository evidence; do not invent missing values.

## Contents

- Strategy request and response
- Escalation packet
- Completion record

## Strategy request and response

Send Sol High a request with this shape:

```json
{
  "schema": "coverage-campaign/strategy-request@1",
  "repository": {
    "git_root": "/absolute/repository",
    "checkout": "/absolute/worktree",
    "branch": "branch-name",
    "revision": "commit",
    "suite": "stable-suite",
    "baseline_snapshot_id": "uuid"
  },
  "batch": {
    "target_case_count": 100,
    "family_count": 10,
    "cases_per_family": 10
  },
  "constraints": [
    "one Luna Max writer",
    "input-driven public behavior",
    "no expected-output or denominator edits"
  ],
  "coverage_targets": [
    {
      "id": "target-1",
      "file_path": "src/example.rs",
      "line_ranges": ["120-137"],
      "metrics": {"uncovered_lines": 12},
      "source_excerpt": "bounded excerpt"
    }
  ],
  "input_surfaces": [
    {
      "public_entrypoint": "library::decode",
      "generator_path": "tests/fixtures/generate.rs",
      "neighboring_test_pattern": "existing-case-family"
    }
  ],
  "validation_lanes": {
    "fast": "registered-fast-command-or-null",
    "coverage": "registered-coverage-command-or-null"
  }
}
```

Require Sol to return:

```json
{
  "schema": "coverage-campaign/strategy@1",
  "request_revision": "commit",
  "reachability_findings": [
    {
      "target_id": "target-1",
      "classification": "reachable",
      "public_path": ["library::decode", "parser", "target branch"],
      "evidence": ["src/example.rs:120", "tests/existing.rs:42"]
    }
  ],
  "families": [
    {
      "id": "family-01",
      "target_ids": ["target-1"],
      "case_ids": ["case-001", "case-002"],
      "input_construction": "deterministic declarative dimensions",
      "expected_regions": ["src/example.rs:120-137"],
      "fast_lane": "registered-fast-command-or-null",
      "coverage_lane": "registered-coverage-command-or-null",
      "risks": ["unsupported public representation"],
      "stop_condition": "public adapter rejects the representation"
    }
  ],
  "readiness_issues": [],
  "rejected_targets": [
    {
      "target_id": "target-2",
      "classification": "unsupported",
      "evidence": ["public type cannot construct required state"]
    }
  ]
}
```

Require exactly the requested total and family partition. `case_ids` may be
compactly generated from declared dimensions, but every ID must be predictable
before execution. `expected_regions` names execution targets, never expected
program output. Copy validation lane names verbatim from the request. When a
lane is `null`, keep it `null`, add a `readiness_issues` entry, and leave command
registration or approval to Luna; never invent a command or target name.

## Escalation packet

Send only bounded failure evidence:

```json
{
  "schema": "coverage-campaign/needs-sol@1",
  "cycle": 1,
  "strategy_family_ids": ["family-01"],
  "baseline_snapshot_id": "uuid",
  "current_snapshot_ids": ["uuid"],
  "runs": [
    {
      "run_id": "uuid",
      "command": "approved-command",
      "status": "failed",
      "log_literals": ["exact bounded failure text"]
    }
  ],
  "changed_files": ["tests/fixtures/generate.rs"],
  "remaining_ranges": ["src/example.rs:120-137"],
  "observed_behavior": "public adapter rejects before parser entry",
  "hypotheses_ruled_out": ["fixture was not selected", "stale artifact"],
  "question": "Find another public representation or classify the target."
}
```

Do not include raw logs, broad source dumps, unrelated diffs, or prior chat.

## Completion record

Record the exact baseline/final snapshots, metric deltas supplied by their
artifacts, per-family proposed/generated/retained/removed/failing counts,
verification commands and statuses, bug classifications, escalation count,
and remaining target IDs. Use `unmeasured` rather than an inferred zero when a
current snapshot, comparable baseline, suite, or attribution run is absent.
