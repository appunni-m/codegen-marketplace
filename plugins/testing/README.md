# Testing

Testing workflows backed by the local
[Coverage MCP](https://github.com/appunni-m/coverage-mcp) server.

Coverage MCP is a native Rust executable. For checkout-local development, run
it through Cargo; this avoids a separate build or install:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

The first invocation may compile bundled DuckDB; warm it with `-- --version`
before connecting if the MCP host has a short startup timeout.

To use that launcher in the local Codex registration, replace the server
explicitly:

```bash
codex mcp remove coverage-mcp
codex mcp add coverage-mcp -- cargo run --locked \
  --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

For a host without the checkout or Cargo, install the native binary. This
plugin does not invoke the Rust repository through `uvx` or `pip`:

```bash
cargo install --git https://github.com/appunni-m/coverage-mcp.git \
  --locked coverage-mcp
coverage-mcp --version
```

The portable plugin's stdio connector runs `coverage-mcp connect` in the MCP
client's current repository. Use an explicit `--repo` when the host does not
provide a repository working directory. The machine-readable connector
declaration is in `compatibility.json`.

The published manifest keeps that native default because an installed plugin
cannot safely infer a user's Coverage MCP checkout. Use the explicit Cargo
manifest option for local development; it never falls back to a guessed path.

```bash
coverage-mcp connect --repo /absolute/path/to/repository
```

## Installation Boundary

The testing plugin installs the `use-coverage-mcp` skill and configures the
stdio connector. The connector opens the selected repository's
`.coverage-mcp/coverage.duckdb`; it does not start an HTTP daemon or copy any
DuckDB. Run `cargo run --locked --manifest-path
<coverage-mcp-checkout>/Cargo.toml -- serve` separately during local
development, or `coverage-mcp serve` for an installed binary, when the
dashboard or HTTP MCP transport is needed.

## Gemini CLI

Gemini accepts one repository-level extension artifact, so this marketplace
declares Coverage MCP in its combined `rust-development` Gemini extension.
Install or update the repository extension, then restart Gemini CLI:

```bash
gemini extensions install https://github.com/appunni-m/codegen-marketplace
```

The extension launches the same native `coverage-mcp` connector and exposes its
tools alongside the Rust development context.

Update the plugin with:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

For local source changes, restart the Cargo-launched connector; no build or
install is required. Update the native server separately for an installed
binary:

```bash
cargo install --git https://github.com/appunni-m/coverage-mcp.git \
  --locked --force coverage-mcp
```

New connectors resolve the updated executable. Existing history remains in each
repository's `.coverage-mcp/coverage.duckdb`.

Verify the local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

For a separately running HTTP daemon, use `curl http://127.0.0.1:59471/health`.
Restart the connector after upstream changes so its tool inventory matches the
updated binary.

After a test or coverage task completes, open
<http://localhost:59471/> in a browser only when a separate `coverage-mcp serve`
process is running; do not open the browser automatically.

Register test commands only after a human approves the complete command,
working directory, and artifact paths.

The plugin includes the `use-coverage-mcp` skill. Codex and other compatible
agents load that skill for test execution, coverage review, artifact lookup,
worktree comparison, and regression investigation. The skill contains the full
agent workflow and explains why Coverage MCP should be used instead of reading
raw logs and reports.

The plugin also includes `run-coverage-campaign` for high-throughput,
input-driven coverage work in Codex. Start the main task on GPT-5.6 Luna with
Max reasoning. The skill keeps Luna as the only writer for implementation,
testing, pruning, and validation, and delegates bounded read-only strategy and
recovery packets to GPT-5.6 Sol with High reasoning. It verifies the Coverage
MCP repository context and baseline before editing, defaults to 100 candidates
in ten attributable families, and stops rather than silently using foreign or
unmanaged coverage evidence.

Coverage MCP `tools/list` describes concrete input and output fields,
nullability, bounds, and status enums for every tool. Agents can discover the
wire contract without source-code context. The server instructions plus
`tools/list` are intended to be sufficient to use the MCP effectively; the
skill supplies the policy and multi-tool workflow around that contract.

Agents start with `project_context(detailed=false)` before rerunning an approved
suite. Run and snapshot responses include timestamps and freshness fields such
as `age_seconds` and `age`.

`run_test` queues long suites and returns a durable run id without holding the
MCP call open. Agents fetch current run state with
`get_run_data(detailed=false)`, wait at least the returned
ETA-aware `poll_after_ms` after each non-terminal response, and reuse one stable
`idempotency_key` for all retries of the same intended run. `get_run_data` is
read-only and only fetches durable run data; `cancel_run` is the separate
mutating tool that stops obsolete work and its process group. Full logs remain
on disk; `search_test_logs` returns only literal matches for one query string or
a list of query strings, plus bounded surrounding lines. `max_words` is the
primary response budget, cursor pagination continues collections, and
`detailed=false` remains the default everywhere.

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
timeout. `poll_after_ms` follows those estimates so agents avoid immediate
repeat polling for long queued or running jobs. Missing-history jobs use a
conservative backoff rather than a one-second heartbeat.

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

The installer uses `coverage-mcp` on `PATH` by default. For local checkout
development, pass the Cargo manifest explicitly; for an installed binary or a
host whose working directory is not the repository, pass a command and repo:

```bash
node /path/to/codegen-marketplace/plugins/testing/scripts/install-pi-mcp.mjs \
  --cargo-manifest /absolute/path/to/coverage-mcp/Cargo.toml \
  --repo /absolute/path/to/repository
```

```bash
node /path/to/codegen-marketplace/plugins/testing/scripts/install-pi-mcp.mjs \
  --command /absolute/path/to/coverage-mcp \
  --repo /absolute/path/to/repository
```

The installer merges `coverage-mcp` into `~/.config/mcp/mcp.json` and preserves
existing servers. Restart Pi after installing the adapter.
