---
name: use-coverage-mcp
description: Use when an agent needs to run tests, inspect coverage, compare worktrees, find missing lines, investigate regressions, retrieve test results, or manage Coverage MCP artifacts.
---

# Use Coverage MCP

Coverage MCP records approved commands, logs, snapshots, and worktree lineage.
Use bounded schema-revision 7 queries instead of direct suites or whole files.

Use `tools/list` for schema; this skill sets policy and token-efficient defaults.

## Preconditions

- Codex uses pinned `coverage-mcp connect`; other hosts may run it directly or
  via `cargo run --locked --manifest-path <checkout>/Cargo.toml -- connect`.
  Never use Python or Node launchers.
- Stdio forwards its repository to port `59471`. Only the daemon holds the
  ownership lease; client connections never lock. A newer connector replaces
  an older owner only when health and its active lease agree; unknown,
  equal/newer, or different-database owners fail closed. Only the daemon opens
  `<shared-git-root>/.coverage-mcp/coverage.duckdb`; connectors have no database
  override.
- Existing stdio bridges recreate a crashed daemon after connection refusal
  and replay that undelivered request once; retry ambiguous failures with the
  same idempotency key.
- Never bypass the ledger or create, copy, or open a database. Return
  `BLOCKED_MCP_CONTEXT` when MCP is unavailable.

## Response Policy

- Keep `detailed=false`. Only `project_context`, `get_run_data`,
  `coverage_query`, and `coverage_compare` expose it; use true only for
  documented audit or provenance data.
- `max_words` is the primary response budget. Choose the smallest useful
  budget and continue collections with the opaque `next_cursor` as `cursor`.
- Never request generic log limits or full stdout/stderr. Use
  `search_test_logs` with one literal query string or a list of literal query
  strings, the smallest useful `context_lines`, and a bounded `max_words`.
- Treat unknown parent IDs as errors. Never reinterpret an empty collection as
  proof that an unknown run, snapshot, worktree, or file exists.

## Discover Before Running

1. Call `project_context(detailed=false)` to read coverage freshness, approved
   commands, `data.latest_run.id`, active runs, and queue state.
2. Decide whether the latest matching result is fresh enough from `age` and
   `age_seconds` before submitting another run.
3. If an intended run is queued or running, retain its run ID and poll it. Do
   not create a duplicate.

## Preserve Human Approval

Run only immutable registered commands whose command, cwd, shell, and artifacts
exactly match the intended execution.

For a new or changed command:

1. Present the complete command, cwd, shell, and artifact definitions.
   Coverage artifacts must declare `coverage_format` and a stable `suite`.
2. Obtain explicit human approval for those exact values.
3. Call `register_test_command` with `human_approved=true`, `approved_by`, a
   specific `approval_note`, and a bounded `max_words`.

## Run Through The Ledger

Call `run_test` with the registration ID or name, `wait=false`, and one stable
`idempotency_key` for the intended execution.

- Save the returned run ID.
- Reuse that key on retries.
- Fetch run state with `get_run_data(detailed=false)` and pass the
  required `run_id` explicitly. To inspect the latest run, use
  `data.latest_run.id` from `project_context`; there is no implicit latest-run
  selection. Read-only; returns durable run data. When
  `terminal` is false, wait at least the returned ETA-aware `poll_after_ms`
  before the next status fetch. Do not poll immediately.
- Cancel only when the user no longer wants the run, using
  `cancel_run(detailed=false)`.
- On failure, use `search_test_logs` for a specific error, failure name,
  summary marker, or small list of related literals. Retrieve another window
  only when the first evidence points to a different literal.
- On terminal state, inspect `coverage_ingest` and declared artifact outcomes
  before making a coverage claim.

Keep `failed`, `cancelled`, `timeout`, `interrupted`, and `internal_error`
distinct; a test failure is result data, not a transport failure.

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

Each call is one narrow projection. Make multiple independent calls, or chain a
dependent call using the exact `snapshot_id`, `file_path`, and line range from
the prior response; never request a raw all-files/all-lines report.

Use `coverage_query` with the smallest view:

1. `view="targets"` for ranked next work; use `order_by` to choose priority,
   uncovered lines, line rate, or file path.
2. `view="summary"` for overall metrics and freshness.
3. `view="insights"` for deterministic priorities.
4. `view="files"` for weak files.
5. `view="file"` for one file's red uncovered regions. Supply `line_ranges`
   only for exact line records; duplicate, nested, overlapping, and adjacent
   ranges normalize.
6. `view="line_history"` for one path and line over time.

Use `coverage_compare(view="regions")` for compact grouped previous-session
impact, `view="files"|"lines"` for an exact audit, and `source_context` only for
bounded ranges already identified by coverage data.

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
missing baseline, and unmeasured coverage distinct. Tell the user the managed
dashboard is available at <http://localhost:59471/> after the task reaches a
terminal state. Do not open the browser automatically.
