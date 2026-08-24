---
name: coverage-review
description: Review managed test results and coverage when running tests, inspecting snapshots, comparing compatible history, finding missing lines, investigating regressions, or reporting coverage evidence.
---

# Coverage Review

Use the repository's managed Coverage MCP evidence to run approved tests,
inspect immutable snapshots, compare compatible lineage, and report
uncertainty. This skill owns workflow decisions; the server owns the wire
schema, validation, freshness, and bounded projections.

## Preconditions

- Start from the active repository context. Never create, copy, open, or edit a
  Coverage MCP database directly.
- If Coverage MCP is unavailable or points at another repository, stop with
  `BLOCKED_MCP_CONTEXT`. Do not silently replace the managed baseline with a
  raw coverage command.
- Keep test failure, coverage regression, absent artifact, parser failure,
  missing baseline, stale evidence, and unmeasured coverage distinct.

## Discover and preserve approval

1. Call `project_context(detailed=false)` first. Read the selected repository,
   freshness, approved commands, and the latest run id in `data.latest_run.id`,
   plus active runs and queue state.
2. Prefer a fresh matching snapshot. Decide whether another run is necessary
   from age, suite, branch, commit, and ingestion state.
3. If the intended command is queued or running, retain its explicit run ID;
   do not create a duplicate.
4. Run only an immutable registered command whose complete command, cwd, shell,
   and artifact definitions match the intended execution.
5. For a new or changed command, present the exact command, cwd, shell,
   artifact paths, coverage format, and suite for human approval. Register it
   only with `human_approved=true`, `approved_by`, and a specific
   `approval_note`. Never invent a command or artifact path.

## Run through the ledger

Call `run_test` with the registration ID or name, `wait=false`,
`reuse_if_unchanged=true`, and one stable `idempotency_key` for a new intended
execution.

- Save the returned `run_id` and reuse the same idempotency key on retries.
- If `submission_reused=true`, use the returned terminal evidence and
  `reuse_reason`; do not launch another run unless the user explicitly asks to
  force execution or the checkout/test inputs changed.
- Poll with `run_review(view="status", run_id=...)`. For every non-terminal
  response, wait at least the returned `poll_after_ms`; never poll immediately
  or infer progress from wall-clock time.
- Use `cancel_run` only when the user no longer wants the run.
- On failure, use `run_review(view="logs", run_id=..., query=...)` with one
  literal error, failure name, summary marker, or small list of related
  literals. Request bounded context, never full logs.
- On terminal state, inspect `coverage_ingest.status`, artifact outcomes, and
  snapshot IDs before making a coverage claim. A terminal response with a
  newly ingested snapshot includes one bounded review; do not repeat it while
  polling.

## Verify evidence and lineage

1. A declared artifact with `coverage_format` is automatically ingested only
   when the managed run created or modified it.
2. Treat `failed`, `missing`, `skipped_stale`, and `skipped_run_status` as
   explicit no-snapshot outcomes. Report the bounded ingestion error.
3. Use an automatically returned snapshot ID directly; do not import the same
   artifact again.
4. Use `coverage_import` only for a repository-relative external or historical
   report that was not produced by the managed run. It records external
   provenance and must be followed by `coverage_review` for analysis.
5. Never claim coverage passed, regressed, improved, or stayed unchanged
   without a valid compatible measurement and an explicit baseline when the
   claim is about change.
6. Prefer `baseline.kind="parent_commit"` or `"ref"` for ordinary Git
   comparisons, `"previous_snapshot"` for the previous compatible measurement,
   `"worktree_base"` only when a durable worktree baseline already exists,
   `"explicit"` for a known snapshot, and `"none"` when no comparison claim is
   desired.

## Choose the smallest useful review

Use the consolidated `coverage_review` tool:

- `task="change"` for changed executable lines, coverage deltas, branch gaps,
  grouped regions, and a server-generated next action;
- `task="history"` for the latest two detailed points plus an aggregate
  window (default ten points);
- `task="insight"` for bounded ranked uncovered regions;
- `task="source"` for up to ten grouped source ranges already identified by
  coverage evidence;
- `task="audit"` or `representation="audit"` only for exact records;
- `task="all"` for a bounded combination of change, history, and insight.
- `find_duplicate_coverage_tests` for bounded groups of named tests with equal
  normalized line, branch, and function observation sets.

Carry exact `measurement.snapshot_id` or `measurement.run_id`, baseline
selectors, file paths, and source ranges from one response into the next.
Independent reviews may run in parallel; dependent source requests wait for the
review that produced their ranges. Keep `max_files`, `max_regions`,
`max_source_lines`, `max_words`, and `max_bytes` small. If a budget error is
returned, reduce the limits or omit source instead of requesting a raw report.

Use `representation="compact"` for many changed ranges. The server emits each
file path once per file group and publishes field-specific legends. In
`changed_code`, `+` means covered added executable, `!` uncovered added
executable, `~` a branch gap, `.` a non-executable addition, and `?` unavailable
or unmeasured coverage. In compact `regions`, `+` means improved or newly
measured, `!` regressed, `-` removed, and `~` changed coverage. Use
`representation="audit"` only when exact records are explicitly needed.
Compact file metrics use one `file_legend` plus `p`, `l`, `b`, `f`, and `r`
arrays rather than repeating metric keys for every file.

For duplicate candidates, pass the matching `snapshot_id` or `suite`, keep the
default small limits, and follow `page.next_cursor`. The result compares
coverage observations only; inspect test logic, inputs, assertions, side
effects, and dependencies before retaining or removing any candidate.

## Report the result

Include only evidence relevant to the user's question:

- command name, terminal status, counters, duration, and freshness;
- repository, checkout, branch, commit, suite, measurement, and baseline;
- line, branch, function, and region metrics supplied by the report;
- grouped newly covered/uncovered or regressed regions;
- `claim_status`, server-provided `reasons`, and `next_action`;
- `source_resolution` when source came from the measured commit or a current
  checkout fallback;
- ingestion status, linked snapshot ID, parser warnings, stale/missing
  artifacts, or an unmeasured state;
- the highest-priority evidence and one bounded next action.

Raw LLVM/LCOV grep can answer a narrow one-off question, but it cannot provide
the server's durable lineage, freshness, run provenance, changed-code
classification, history normalization, or bounded token-efficient envelope.
Use raw files only when the user explicitly asks for an independent parser
check, and label that evidence separately from managed Coverage MCP evidence.

The managed dashboard is available at <http://localhost:59471/> after a
terminal run. Do not open the browser automatically.
