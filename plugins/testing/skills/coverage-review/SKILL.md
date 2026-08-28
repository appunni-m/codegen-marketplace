---
name: coverage-review
description: This skill should be used when an agent needs to "run managed tests", "run an incremental coverage case", "compare coverage snapshots", "inspect coverage regressions", or report bounded coverage evidence.
---

# Coverage Review

Use managed Coverage MCP evidence for approved execution, immutable snapshots,
compatible comparisons, and bounded reporting. The skill owns workflow choices;
the server owns schema, validation, freshness, lineage, and projections.

## Preconditions

- Start from the active repository context. Never access a Coverage MCP database
  directly.
- If MCP is unavailable or points at another repository, stop with
  `BLOCKED_MCP_CONTEXT`; do not substitute a raw coverage command.
- Keep test failure, artifact/parser failure, coverage regression, missing or stale evidence, missing baseline, and unmeasured coverage distinct.

## Discover approval and the command

1. Call `project_context(detailed=false)` first. Read the selected repository,
   freshness, approved commands, the `latest run` id in `data.latest_run.id`,
   active runs, and queue state.
2. Prefer a fresh matching snapshot. If the intended command is queued or
   running, keep its explicit run ID and do not create a duplicate.
3. Run only a complete immutable registration whose command, cwd, shell, and
   artifacts match the intended case. Register one command once; do not create
   a command for every filter or case-specific argument.
4. For a new or changed command, show the exact command, cwd, shell, artifact
   paths, format, and suite for approval. Register only with
   `human_approved=true`, `approved_by`, and a specific `approval_note`.

## Run through the ledger

Call `run_test` with the registration ID/name, `wait=false`,
`reuse_if_unchanged=true`, and a stable `idempotency_key`. Optional
`arguments` are case-specific strings. The server shell-quotes them and either
replaces one approved `{{args}}` placeholder or appends them. The argument
boundary must be part of the human-approved command; never guess a filter or
register another command for it.

For a full run, omit `execution` and `baseline` or use
`execution.mode="full"`. For a smaller incremental case:

```json
{
  "command_ref": "coverage-tests",
  "arguments": ["--filter", "parser::handles_empty_input"],
  "execution": {"mode": "incremental", "label": "parser empty input"},
  "baseline": {"kind": "explicit", "snapshot_id": "<fixed-base-snapshot-id>"},
  "reuse_if_unchanged": true,
  "idempotency_key": "parser-empty-input-v1"
}
```

`execution.identity` is optional. Coverage MCP fingerprints mode, arguments,
and the explicit baseline, then persists that context; agents do not calculate
or invent a hash. Use a different idempotency key for each materially different
case. Test selection comes only from the approved command's argument interface.

Obtain `<fixed-base-snapshot-id>` from exactly one ID in a completed full run's
`data.coverage_ingest.snapshot_ids`, or from a repository-compatible
`coverage_import` result. Carry it explicitly into every incremental run. Never
infer it from the latest/previous snapshot or substitute command, suite, branch,
cwd, or case label.

- Save `run_id`; reuse the same `idempotency_key` on retries.
- If `submission_reused=true`, use its terminal evidence and `reuse_reason`.
- Poll `run_review(view="status", run_id=...)` only after the returned
  `poll_after_ms`; do not infer progress from elapsed time.
- Use `cancel_run` only when the user no longer wants the run. On failure, use
  `run_review(view="logs", run_id=..., query=...)` with bounded literal matches.
- On terminal state, inspect `coverage_ingest.status`, artifact outcomes, and snapshot IDs. An incremental run automatically includes `incremental_review` after ingestion; when multiple ordinary artifacts are declared, its standard `measurement` is the deduplicated baseline-union of all selected snapshots, with run-specific data under `incremental`. `run_review(view="status")` exposes it again. `pending` means not finished; `not_measured` plus `reasons` means no coverage claim is available. Do not launch another review runner call.

## Incremental versus standalone comparison

An incremental run is execution plus review: the selected subset runs through
the existing approved command, one or more reports are ingested, and the server
forms the deduplicated union of the selected snapshots with the explicit base.
The standard top-level `measurement` and `baseline` have the same shape as a full review. `incremental.run` preserves selected-run provenance, while
`incremental.metric_deltas`, `coverage_gain`, `merge`, and the nested `diff`
carry run-specific increment/decrement data and replacement diagnostics. Use
the server-provided union counts and rates; never reconstruct an x/y rate from
the selected run. For a selected subset, baseline identities absent from that
subset are `not_observed`, not regressions; only `complete_snapshot` supports a
real regression claim.

Use `coverage_review(task="incremental")` only when stored measurements already
exist and an independent comparison is needed. It requires
`measurement.snapshot_id` or a `measurement.run_id` resolving to ordinary
artifact snapshots, plus `baseline.kind="explicit"` and the matching
`baseline.snapshot_id`. It never selects a previous snapshot, invokes a runner,
reparses a report, or reruns tests.

Keep the base immutable and record its ID. Use artifact
`detail_retention="incremental_base"` for a long-lived high-detail base.
Compaction remains compatible: it preserves IDs and restores detail from the
zstd payload; `incremental.detail_source` reports `relational` or
`compacted_payload`. A format without named observations has unavailable test
attribution, not a coverage gain/regression. Incompatible repositories or
normalized formats produce `claim_status="not_measured"` with server reasons.

## Composite production coverage

Treat composite coverage as a normal managed run, not a second command or review
workflow. Register one approved command with exactly one required inventory
artifact and one descriptor for every component/package variant. Coverage
descriptors declare `component_id`, `package_variant`, `language`, `format`,
`inventory_artifact`, `role="coverage"`, and explicit `{path,logical_source_id}`
aliases; declare `role="inventory"` for the authoritative inventory. Never
infer aliases, variants, or identity from filenames, paths, or suite names.
For full composite coverage, use the registered command with approved
arguments and no baseline. For a smaller case, reuse it with approved
`arguments`, `execution.mode="incremental"`,
`baseline.kind="explicit"`, and `baseline.composite_snapshot_id`.
Save `data.composite_snapshot_id` from every completed composite run. The
terminal incremental run automatically exposes `incremental_review`; do not
launch a second comparison. Use standalone
`coverage_review(task="incremental")` only for existing composite snapshots,
with `measurement.composite_snapshot_id` and
`baseline.composite_snapshot_id`. Do not mix selector types.

Treat the inventory as the canonical production-region denominator. Every
variant must be present, fresh, well-formed, and source-compatible; missing or
invalid evidence leaves the composite incomplete and never reduces the
denominator. Report the exact rate, covered/total regions, Rust/WGSL, Python,
and JavaScript summaries, blocking reasons, and remediation buckets. Aggregate
coverage remains valid when named-test attribution is `unavailable`.

Composite incremental review compares stored canonical-region rows and child
observations only; it requires matching repository, mapping version, and
inventory hash. Compaction preserves composite rows and restores child detail
from the compacted payload; report the detail source. Mark long-lived base
artifacts `detail_retention="incremental_base"` to minimize restoration work.
## Evidence and lineage

1. Automatic ingestion requires a declared `coverage_format` artifact created or
   modified by the managed run. `failed`, `missing`, `skipped_stale`, and
   `skipped_run_status` are explicit no-snapshot outcomes.
2. Use the returned snapshot ID directly; do not import that artifact again.
3. Use `coverage_import` only for an external or historical repository-relative
   report, then use `coverage_review`.
4. Do not claim coverage passed, regressed, improved, or stayed unchanged
   without a valid compatible measurement and explicit baseline for change.
5. For ordinary Git comparison prefer `parent_commit`, `ref`, or
   `previous_snapshot`; use `worktree_base` only for a durable worktree base,
   `explicit` for a known snapshot, and `none` when no change claim is wanted.
   Composite comparisons use only explicit composite snapshot IDs and matching
   inventory provenance.

## Choose a bounded review

Use `coverage_review` with the smallest task: `change` for changed executable
lines and regressions; `incremental` for explicit current-vs-base ordinary or
composite stored detail; `history` for recent points plus an aggregate;
`insight` for ranked gaps; `source` for bounded ranges; `audit` for exact
records; and `all` for a bounded combination. Use
`find_duplicate_coverage_tests` for coverage-equivalent named test candidates
only; it does not compare logic or authorize deletion.

Carry exact measurement, baseline, file, and source identifiers forward. Keep
`max_files`, `max_regions`, `max_test_ids`, `max_source_lines`, `max_words`,
and `max_bytes` small. If a budget error occurs, reduce limits or omit source.
Use `representation="compact"` for many ranges and `audit` only for exact
records. `claim_status`, `reasons`, `next_action`, `source_resolution`, and
truncation metadata are authoritative.

## Report the result

Report the command and terminal state, duration/freshness, repository and
provenance, all supplied line/branch/function/region metrics, grouped gain or
regression regions, ordinary or composite measurement/baseline IDs, ingestion
status, parser warnings, artifact state, `claim_status`, server `reasons`, and
one bounded next action. For composite results, include the canonical-region
denominator, three component summaries, completeness/remediation reasons, and
attribution status. Label raw LLVM/LCOV inspection separately; it cannot
replace managed lineage or the bounded `coverage_review` envelope. The dashboard is available at <http://localhost:59471/> after a terminal run; Do not open the browser automatically.
