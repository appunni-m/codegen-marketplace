# Testing

Testing workflows backed by the local
[Coverage MCP](https://github.com/appunni-m/coverage-mcp) server.

The plugin launches a lightweight stdio connector with `uvx`. The connector
installs Coverage MCP from its public HTTPS Git repository, starts or reuses
one user-level HTTP daemon, and selects the agent's Git repository lazily.
The source is deliberately tracked from upstream `main`; the machine-readable
connector declaration is in `compatibility.json`.

```bash
uvx --from git+https://github.com/appunni-m/coverage-mcp.git@main \
  coverage-mcp connect
```

## Installation Boundary

The testing plugin installs the `use-coverage-mcp` skill and configures the
stdio connector. `uvx` manages its isolated Python environment; the connector
starts the HTTP daemon on demand. The plugin does not copy any DuckDB.

## Gemini CLI

Gemini accepts one repository-level extension artifact, so this marketplace
declares Coverage MCP in its combined `rust-development` Gemini extension.
Install or update the repository extension, then restart Gemini CLI:

```bash
gemini extensions install https://github.com/appunni-m/codegen-marketplace
```

The extension launches the same `uvx` connector and exposes its tools alongside
the Rust development context.

Update the plugin with:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Update the server separately:

```bash
python -m pip install --upgrade \
  "coverage-mcp @ git+https://github.com/appunni-m/coverage-mcp.git@main"
```

New connectors resolve the updated package. Existing history remains in each
repository's `.coverage-mcp/coverage.duckdb`.

Verify the running version:

```bash
curl http://127.0.0.1:59471/health
```

The response must include `version`; `common_db_path` must identify the daemon
registry, and `run_concurrency` reports the active worker count. Restart the
connector after upstream changes so its tool inventory matches `main`.

After a test or coverage task completes, open
<http://localhost:59471/> in a browser to view progress, run history, and
coverage details.

Register test commands only after a human approves the complete command,
working directory, and artifact paths.

The plugin includes the `use-coverage-mcp` skill. Codex and other compatible
agents load that skill for test execution, coverage review, artifact lookup,
worktree comparison, and regression investigation. The skill contains the full
agent workflow and explains why Coverage MCP should be used instead of reading
raw logs and reports.

Coverage MCP `tools/list` describes concrete input and output fields,
nullability, bounds, and status enums for every tool. Agents can discover the
wire contract without source-code context. The server instructions plus
`tools/list` are intended to be sufficient to use the MCP effectively; the
skill supplies the policy and multi-tool workflow around that contract.

Agents start with `project_context(detailed=false)` before rerunning an approved
suite. Run and snapshot responses include timestamps and freshness fields such
as `age_seconds` and `age`.

`run_test` queues long suites and returns a durable run id without holding the
MCP call open. Agents poll `test_run(action="status", detailed=false)` at
`poll_after_ms` and reuse one stable `idempotency_key` for all retries of the
same intended run. `test_run(action="cancel")` stops obsolete work and its
process group. Full logs remain on disk; `search_test_logs` returns only literal
matches for one query string or a list of query strings, plus bounded
surrounding lines. `max_words` is the primary response budget, cursor
pagination continues collections, and `detailed=false` remains the default
everywhere.

`coverage_query(view="file")` returns compact metrics and grouped coverage gaps.
Request bounded `line_ranges` only when exact covered line records are needed;
duplicate, nested, overlapping, and adjacent windows are normalized.

Artifacts registered with `coverage_format` are automatically ingested when a
managed run creates or modifies them. Terminal run responses report
`coverage_ingest.status`, immutable `snapshot_ids`, and per-artifact parser
outcomes. Agents use those snapshot IDs directly and reserve
`ingest_coverage` for external or historical reports.

After a command has natural completion history, polls include a median ETA,
p90 reference, sample count, and estimated timestamps. Queue ETA schedules known
FIFO work across the server's worker lanes. Missing history is explicit, and an
overrun is reported separately so agents do not mistake a median estimate for a
timeout.

The server runs four approved commands concurrently by default. Set
`COVERAGE_MCP_RUN_CONCURRENCY` to 1-32 before startup; use `1` when suites share
non-isolated outputs and cannot overlap safely.

The server keeps the newest 100 terminal runs per approved command by default.
Set `COVERAGE_MCP_RUN_RETENTION` before server startup to change this count-based
limit. Coverage snapshots and registered artifact files are not pruned with run
history.

## Pi

Pi does not include an MCP client. Install the testing skill and MCP adapter, then register Coverage MCP in Pi's shared
MCP configuration:

```bash
pi install /path/to/codegen-marketplace/plugins/testing
pi install npm:pi-mcp-adapter
node /path/to/codegen-marketplace/plugins/testing/scripts/install-pi-mcp.mjs
```

The installer merges `coverage-mcp` into `~/.config/mcp/mcp.json` and preserves
existing servers. Restart Pi after installing the adapter.
