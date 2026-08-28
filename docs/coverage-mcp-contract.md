# Coverage MCP contract

Status: schema revision 16, eight public tools, and the exact tools-list digest
are implemented by the canonical Rust server and pinned in
`plugins/testing/compatibility.json`. The canonical server's
[README and source](https://github.com/appunni-m/coverage-mcp) are the source
of truth for wire semantics, validation, storage, freshness, provenance, and
response budgets.

The marketplace owns workflow guidance in the
[`coverage-review` skill](../plugins/testing/skills/coverage-review/SKILL.md).
The server owns the MCP schema and implementation. Keep this document limited
to the integration boundary; do not copy the server's complete schema here.

## Public inventory

The active inventory contains exactly:

- `project_context`
- `register_test_command`
- `run_test`
- `run_review`
- `cancel_run`
- `coverage_import`
- `coverage_review`
- `find_duplicate_coverage_tests`

Both HTTP and native stdio use the same JSON-RPC dispatcher. The expected
schema revision, tool count, and `tools/list` SHA-256 digest are pinned in the
compatibility record and verified against a live server by
`pnpm check:coverage-mcp`.

## Run and incremental-review boundary

Register one exact human-approved command, then reuse it with optional
case-specific `run_test.arguments`. The arguments are persisted with the run,
shell-quoted, and either replace one approved `{{args}}` placeholder or append
to the approved command. A new test filter does not require registering a new
command.

An incremental run supplies:

```json
{
  "command_ref": "coverage-tests",
  "arguments": ["--filter", "parser::handles_empty_input"],
  "execution": {"mode": "incremental", "label": "parser empty input"},
  "baseline": {"kind": "explicit", "snapshot_id": "<snapshot-id>"}
}
```

`execution.identity` is optional. The server fingerprints mode, arguments,
and the explicit baseline, so idempotency and unchanged-run reuse cannot cross
case boundaries. An incremental `run_test` automatically attaches a bounded
`incremental_review` after terminal ingestion. If a run declares multiple
ordinary coverage artifacts, their `snapshot_ids` form one selected measurement
set. The standard `data.measurement` and `data.baseline` use the same shape as
full mode. `data.measurement` is the deduplicated union of the fixed baseline
and every selected snapshot; `data.incremental.run` preserves selected-run
provenance, while `metric_deltas`, `coverage_gain`, `merge`, and `diff` carry
increment/decrement evidence. `run_review(view=status)` exposes the same
durable result. Consumers use the server-provided counts and rates rather than
reconstructing an x/y rate from the selected run.

Incremental review keeps two blocks: the additive union is the coverage result,
while `incremental.diff` is a replacement-style diagnostic. For a selected
subset, baseline identities absent from that subset are `not_observed`, not
regressions; only a `complete_snapshot` measurement supports a real regression
claim.

`coverage_review(task="incremental")` is the standalone comparison path for
two already stored snapshots. It requires an explicit current measurement and
an explicit baseline, never selects the previous snapshot, and never invokes a
runner or reparses either report. Both sides must have compatible repositories
and normalized formats. Compacted detail remains usable and identifies its
source in the response.

## Composite coverage boundary

Schema 16 also supports composite production coverage in managed runs. Register
one command with one required inventory artifact and one coverage descriptor for
each declared component/package variant. Every full and incremental `run_test`
uses that same registration; only the approved optional `arguments`, execution
mode, and explicit baseline vary by case. A composite run returns its ordinary
child snapshot IDs plus `data.composite_snapshot_id`.

Composite descriptors must declare `component_id`, `package_variant`,
`language`, `format`, `inventory_artifact`, `role`, and explicit
`logical_source_aliases`. The inventory is the authoritative canonical-region
denominator; matching paths or filenames never deduplicate evidence, and every
declared variant must be present, fresh, well-formed, and source-compatible.
Missing or incompatible evidence leaves the composite incomplete and does not
shrink its denominator.

Use `baseline.composite_snapshot_id` for an incremental composite run and keep
the fixed composite ID immutable. Standalone `coverage_review(task="incremental")`
accepts matching composite measurement and baseline selectors, compares stored
canonical-region rows and child observations without rerunning tests, and
requires the same repository, mapping version, and inventory hash. Compaction
preserves composite rows and restores ordinary child detail from its compacted
payload when attribution is needed; named-test attribution is explicitly
unavailable when the producer did not emit named observations.

## Workflow ownership

The marketplace skill owns approval, polling, freshness, lineage, response
budget, and reporting policy. The server still advertises a self-describing
workflow through `initialize` instructions and `tools/list` descriptions, and
enforces identical behavior over HTTP and stdio, including `source_resolution`
and `max_bytes` validation.

Use `coverage_import` only for an external or historical repository-relative
report. Use `coverage_review` for bounded change, incremental, history,
insight, source, audit, or combined analysis. Use
`find_duplicate_coverage_tests` for bounded coverage-equivalence candidates;
it does not compare test logic or authorize deletion.

## Verification

```sh
pnpm check
pnpm check:coverage-mcp
```

The production binary release pinned by the testing plugin is Coverage MCP
`0.15.3`. Publish or enable that pin only after the matching crates.io/GitHub
release assets, checksums, and live HTTP/stdio contract checks exist.
