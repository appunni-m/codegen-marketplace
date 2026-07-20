---
name: use-coverage-mcp
description: Use when an agent needs to run or review tests, inspect coverage, compare a worktree with its baseline, find missing lines, investigate a regression, retrieve a previous test result, or manage test artifacts through Coverage MCP.
---

# Use Coverage MCP

Coverage MCP is the local system of record for approved test commands, retained
logs, coverage snapshots, and worktree lineage. Use its bounded schema-revision
7 queries instead of running suites directly or loading whole logs, reports, and
source files into model context.

Use `tools/list` for the exact wire schema. This skill defines the workflow,
trust boundaries, and token-conscious defaults.

## Preconditions

- The connector resolves Coverage MCP from upstream `main`; do not impose a
  release-version range in this plugin.
- Verify `/health` reports `schema_revision: 7`, `version`, and
  `common_db_path`. Do not support older schemas or tool aliases.
- One user-level daemon lazily owns one
  `<shared-git-root>/.coverage-mcp/coverage.duckdb` per repository. Linked
  worktrees share that store.
- Never create a daemon or DuckDB per agent/worktree, copy a DuckDB, or bypass
  the approved run ledger when MCP is unavailable.

## Response Policy

- Keep `detailed=false` everywhere by default. Only `project_context`,
  `test_run`, `coverage_query`, and `coverage_compare` expose it; set it true
  once only when their descriptions identify required audit or provenance data.
- `max_words` is the primary response budget. Choose the smallest useful
  budget and continue collections with the opaque `next_cursor` as `cursor`.
- Never request generic log limits or full stdout/stderr. Use
  `search_test_logs` with one literal query string or a list of literal query
  strings, the smallest useful `context_lines`, and a bounded `max_words`.
- Treat unknown parent IDs as errors. Never reinterpret an empty collection as
  proof that an unknown run, snapshot, worktree, or file exists.

## Discover Before Running

1. Call `project_context(detailed=false)` to read coverage freshness, approved
   commands, the latest run, active runs, and queue state.
2. Decide whether the latest matching result is fresh enough from `age` and
   `age_seconds` before submitting another run.
3. If an intended run is queued or running, retain its run ID and poll it. Do
   not create a duplicate.

Repository identity follows the shared Git root. Exact checkout, branch,
commit, suite, and worktree provide the narrower execution lineage.

## Preserve Human Approval

Run only immutable registered commands whose command, cwd, shell, and artifacts
exactly match the intended execution.

For a new or changed command:

1. Present the complete command, cwd, shell, and artifact definitions.
   Coverage artifacts must declare `coverage_format` and a stable `suite`.
2. Obtain explicit human approval for those exact values.
3. Call `register_test_command` with `human_approved=true`, `approved_by`, a
   specific `approval_note`, and a bounded `max_words`.

Changing execution details requires a new immutable registration.

## Run Through The Ledger

Call `run_test` with the registration ID or name, `wait=false`, and one stable
`idempotency_key` for the intended execution.

- Save the returned run ID.
- Reuse the same idempotency key for every retry of that intended run.
- Poll `test_run(action="status", detailed=false)` no faster than
  `poll_after_ms` until `terminal` is true.
- Read queue position and ETA from compact run state or `project_context`.
- Cancel only when the user no longer wants the run, using
  `test_run(action="cancel", detailed=false)`.
- On failure, use `search_test_logs` for a specific error, failure name,
  summary marker, or small list of related literals. Retrieve another window
  only when the first evidence points to a different literal.
- On terminal state, inspect `coverage_ingest` and declared artifact outcomes
  before making a coverage claim.

Test failure is result data, not a transport failure. Keep `failed`,
`cancelled`, `timeout`, `interrupted`, and `internal_error` distinct.

## Verify Coverage Output

1. Read terminal `coverage_ingest.status` and `snapshot_ids`.
2. A declared coverage artifact is freshness-checked and automatically
   ingested when the run creates or modifies it. Failed tests may still produce
   a valid snapshot.
3. Use the returned snapshot ID directly with `coverage_query`. Never ingest
   that artifact again.
4. Treat `failed`, `missing`, `skipped_stale`, and `skipped_run_status` as
   explicit no-snapshot outcomes and report the bounded ingestion error.
5. Use `ingest_coverage` only for an external or historical report not produced
   by `run_test`.

Never claim coverage passed, regressed, improved, or stayed unchanged without a
valid snapshot.

## Maintain Worktree Lineage

Create reference-branch suite snapshots before `register_worktree`. Retain the
returned `worktree_id`; registration freezes the available suite baselines.

- Use `coverage_compare(view="progress", worktree_id=..., suite=...,
  detailed=false)` for compact progress.
- Use `coverage_compare(view="files"|"lines", worktree_id=..., suite=...,
  detailed=false)` for exact regressions.
- For direct comparison, pass explicit current and baseline snapshot IDs.
- Never compare different repositories, suites, or worktree lineages, and
  never use a snapshot predating worktree registration.
- No current worktree snapshot means "not measured", not "unchanged".

## Investigate With Bounded Queries

Use `coverage_query` with the smallest view:

1. `view="summary"` for overall metrics and freshness.
2. `view="insights"` for deterministic priorities.
3. `view="files"` for weak files.
4. `view="file"` for grouped gaps. Supply `line_ranges` only for exact covered
   line records; duplicate, nested, overlapping, and adjacent ranges normalize.
5. `view="line_history"` for one path and line over time.

Use `coverage_compare(view="files"|"lines")` for changed coverage and
`source_context` only for bounded ranges already identified by coverage data.
Paths do not follow renames.

## Report The Result

Report only the fields needed for the task, including:

- command name, terminal status, counters, duration, and freshness
- exact checkout, branch, commit, and suite when relevant
- line, branch, function, and region metrics supplied by the report
- delta against the explicit or frozen baseline
- newly covered/uncovered lines and the highest-priority evidence
- automatic ingestion outcome and linked snapshot ID
- parser warnings, missing/stale artifacts, or missing baseline/current state

Keep test failure, coverage regression, absent artifact, parser failure,
missing baseline, and unmeasured coverage distinct. After the managed task reaches a terminal state, tell the user the dashboard is available at
<http://localhost:59471/>. Do not open the browser automatically.
