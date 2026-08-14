# Testing

Testing workflows backed by the local
[Coverage MCP](https://github.com/appunni-m/coverage-mcp) server.

Coverage MCP is a native Rust executable. Codex launches the bundled
`./bin/coverage-mcp-launcher`, which reuses an exact 0.8.1 binary from
`COVERAGE_MCP_BIN`, `PATH`, or `~/.coverage-mcp/runtime/0.8.1`. On a cache miss,
one launcher acquires `.install-0.8.1.lock`, installs the exact published crate
with Cargo, and all waiting sessions reuse it. The MCP startup timeout is 900
seconds for that first compile; later sessions start from the cache.

Cargo must already be installed, just as `npx` requires Node or `uvx` requires
its own runtime. The plugin does not install Rust and does not fall back to an
unpinned Git branch. Set `COVERAGE_MCP_RUNTIME_DIR` to relocate its cache.
`COVERAGE_MCP_BOOTSTRAP_TIMEOUT_SECONDS` changes the default 900-second wait for
another first-session install; the MCP host startup timeout must be at least as
large.

The bundled launcher is POSIX `sh` and supports macOS, Linux, and WSL. Native
Windows bootstrap is not currently claimed; install the pinned crate manually,
disable the bundled server, and register the absolute
`coverage-mcp.exe connect` command with the MCP host.

For checkout-local development, run Coverage MCP through Cargo; this avoids a
separate build or install:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

The first invocation may compile bundled DuckDB; warm it with `-- --version`
before connecting if the MCP host has a short startup timeout.

The plugin-bundled server and a global `codex mcp` registration are separate.
For checkout-local development, first disable the bundled server in
`~/.codex/config.toml`:

```toml
[plugins."testing".mcp_servers.coverage-mcp]
enabled = false
```

Then register the Cargo launcher globally:

```bash
codex mcp remove coverage-mcp
codex mcp add coverage-mcp -- cargo run --locked \
  --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

Remove the global registration and re-enable the bundled server when returning
to the installed binary so Codex does not load two copies of the tool set.

For another host, or to prewarm Codex, install the published native binary.
This plugin does not invoke Coverage MCP through `uvx`, `pip`, Node, or `npx`:

```bash
cargo install coverage-mcp --version '=0.8.1' --locked
coverage-mcp --version
```

The Codex bootstrap ultimately runs `coverage-mcp connect` in the MCP client's
current repository. The connector starts or reuses the daemon on
`127.0.0.1:59471` and routes the current Git repository to it. Only the daemon
process holds its ownership lease; stdio bridges and direct HTTP clients do not
lock one another. The daemon
remains available after an individual connector exits. Use an explicit
`--repo` for native host configurations that do not provide a repository
working directory. The bundled connector is in `.mcp.json`, and the
machine-readable bootstrap/runtime contract is in `compatibility.json`.

The published Codex manifest keeps the runtime version pinned because an
installed plugin cannot safely infer a user's Coverage MCP checkout or track a
moving Git branch. Use the explicit Cargo manifest option for local
development; it never falls back to a guessed path. Do not publish this plugin
version until Coverage MCP 0.8.1 exists on crates.io.
This plugin revision is synchronized with Coverage MCP schema revision 7 and
its eleven-tool inventory; verify those values through `GET /health` and
`tools/list` after upgrading.

```bash
coverage-mcp connect --repo /absolute/path/to/repository
~/.coverage-mcp/runtime/0.8.1/bin/coverage-mcp connect \
  --repo /absolute/path/to/repository
```

## Installation Boundary

The testing plugin installs the `use-coverage-mcp` skill, its Cargo bootstrap,
and the stdio connector. Racing cache misses serialize only the Cargo install
through the versioned installer lock, which is released before startup. Normal
`connect` processes are lightweight bridges; they do not open DuckDB or take
the daemon ownership lease. The first bridge starts the daemon, whose process
alone holds `<common-db-parent>/daemon.lock` while listening on the fixed
default port `59471`. Any number of HTTP clients and stdio bridges may connect
concurrently, subject to configured runtime limits. The daemon lazily opens the
selected repository's
`.coverage-mcp/coverage.duckdb`, so multiple projects can connect concurrently
without becoming competing database owners. Explicit `connect --db` remains
standalone mode.

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

Start a new Codex task after reinstalling so the task loads the refreshed
skills and bundled MCP connector.

For local source changes, stop the old Cargo-launched daemon; the next connector
starts the rebuilt checkout without an install. Update a manually installed
native binary separately after a published release:

```bash
cargo install coverage-mcp --version '=0.8.1' --locked --force
```

After stopping the old daemon, new connectors resolve the updated executable.
Existing history remains in each repository's
`.coverage-mcp/coverage.duckdb`.

Verify the local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

After `connect` has started, use `curl http://127.0.0.1:59471/health`. Stop the
old daemon after updating the binary; the next connector automatically starts
the new one so its tool inventory matches.

After a test or coverage task completes, the managed dashboard is available at
<http://localhost:59471/>; do not open the browser automatically.

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

## Support and security

- Report Coverage MCP runtime bugs in the
  [Coverage MCP issue tracker](https://github.com/appunni-m/coverage-mcp/issues).
- Report plugin packaging or documentation bugs in the
  [marketplace issue tracker](https://github.com/appunni-m/codegen-marketplace/issues),
  and follow its
  [contribution guide](https://github.com/appunni-m/codegen-marketplace/blob/main/CONTRIBUTING.md).
- Report suspected vulnerabilities privately through the
  [Coverage MCP security policy](https://github.com/appunni-m/coverage-mcp/security/policy)
  rather than a public issue.
