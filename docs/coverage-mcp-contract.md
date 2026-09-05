# Coverage MCP contract

The native Rust server owns the full protocol and storage contract. This
marketplace owns connector configuration and pins compatibility in
[`plugins/testing/compatibility.json`](../plugins/testing/compatibility.json).

Coverage MCP 0.16.0 uses schema revision 18 and two read-only tools:

| Tool | Purpose | Inputs |
| --- | --- | --- |
| `coverage_gaps` | Find a few missing function/region locations | Report or snapshot, literal query, optional line/metric, limit/offset |
| `coverage_compare` | Explain measured changes and remaining gaps | Explicit current/baseline, query/metric, scope, previous batches, limit |

Report-file queries do not import data. Saved ordinary and composite snapshots
remain readable, including compacted detail and missing-component states.
There are no public execution, command-registration, polling, source-reading,
worktree, duplicate-test, or topology endpoints. Resources are empty.

The normal workflow is report → gaps → `rg` and bounded local source reads →
existing test command → explicit comparison. Five groups with at most three
locations each are returned by default. The 12 KiB envelope cap bounds output,
not evidence used for comparison. Narrow the query before paging. Evidence
appears once in `structuredContent`; there is no duplicate JSON text block.

Source/build receipts bind report bytes to measured inputs. Without receipts,
coordinate changes are limited evidence. A current-source mismatch requires
matching source or remeasurement. Selected-test absences are not regressions;
full regression claims require matching full-scope receipts. Failed tests,
unavailable metric detail, and missing artifacts remain explicit. Coverage gain
alone cannot prove test uniqueness or redundancy.

With `scope: "incremental"`, compare only the new tests' report against the saved
baseline. Optional `previous` includes up to 16 earlier batches. Results show
marginal gain, overlap, fixed-denominator combined coverage, and remaining gaps.
Repeated locations count once. Filters affect displayed locations only. Failed
or incompatible reports have no combined total; missing identity is labeled an
unverified estimate. The dashboard uses these same fields and can retain a
verified batch in its earlier-batch selector. Full-suite regression remains
unchecked. See the [server incremental guide](https://github.com/appunni-m/coverage-mcp/blob/main/docs/user-guide.md#run-only-the-new-tests).

HTTP and stdio share one dispatcher. The dashboard uses the same query results
without automatic polling. Optional REST archival administration remains in the
[server HTTP reference](https://github.com/appunni-m/coverage-mcp/blob/main/docs/http-api.md).

Validate the local contract with `pnpm check:coverage-mcp` after installing the
matching binary. Run `pnpm check` for marketplace checks. For future updates,
publish the pinned runtime and native archives before distributing the plugin;
these checks do not publish releases.
