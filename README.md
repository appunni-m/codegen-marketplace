# Codegen Marketplace

Curated software-engineering plugins for Codex, Claude Code, Cursor, Gemini
CLI, Kiro, Vercel Skills CLI, and Pi.

Built with the
[`@ai-plugin-marketplace`](https://github.com/ai-plugin-marketplace/tools)
toolkit from the
[`ai-plugin-marketplace/template`](https://github.com/ai-plugin-marketplace/template).

## Plugins

| Plugin | Purpose | Targets |
| --- | --- | --- |
| `rust-development` | Rust implementation, debugging, documentation, crate research, coding standards, and unsafe review | Claude Code, Codex, Cursor, Gemini CLI, Kiro, Vercel Skills CLI, Pi |
| `testing` | Human-approved test runs, bounded summaries, coverage history, worktree comparisons, and model-routed input campaigns | Claude Code, Codex, Gemini CLI (combined extension), Pi |
| `opensource` | Evidence-first README, source API, contributor, security, release, and packaged-documentation guidance | Claude Code, Codex, Cursor, Vercel Skills CLI, Pi |

## Install

Install only the plugins needed for a given agent.

### Codex

```bash
codex plugin marketplace add appunni-m/codegen-marketplace
codex plugin add rust-development@codegen-marketplace
codex plugin add testing@codegen-marketplace
codex plugin add opensource@codegen-marketplace
```

Start a new Codex thread after installation.

### Claude Code

```bash
claude plugin marketplace add appunni-m/codegen-marketplace
claude plugin install rust-development@codegen-marketplace
claude plugin install testing@codegen-marketplace
claude plugin install opensource@codegen-marketplace
```

Start a new Claude Code session after installation.

### Cursor

Import the marketplace repository in **Settings > Plugins**:

```text
https://github.com/appunni-m/codegen-marketplace
```

The Cursor target currently contains `rust-development` and `opensource`.

### Gemini CLI

```bash
gemini extensions install https://github.com/appunni-m/codegen-marketplace
```

Gemini has one repository-level extension slot, owned by `rust-development`.
The combined extension also exposes Coverage MCP through the native
`coverage-mcp` executable, so install that binary before starting Gemini.
Restart Gemini CLI after installation or update.

### Kiro

Open the Powers panel and add:

```text
https://github.com/appunni-m/codegen-marketplace
```

Kiro has one repository-level power slot, owned by `rust-development`.

### Vercel Skills CLI

```bash
npx skills add appunni-m/codegen-marketplace
```

### Pi

Pi installs local plugin directories. Clone the marketplace once:

```bash
git clone https://github.com/appunni-m/codegen-marketplace.git
pi install ./codegen-marketplace/plugins/rust-development
pi install ./codegen-marketplace/plugins/testing
pi install ./codegen-marketplace/plugins/opensource
```

The testing plugin also needs Pi's MCP adapter because Pi does not expose MCP as
a native marketplace target:

```bash
pi install npm:pi-mcp-adapter
node ./codegen-marketplace/plugins/testing/scripts/install-pi-mcp.mjs
```

Restart Pi after installing the adapter.

## Coverage MCP

The `testing` plugin launches a native stdio connector for
[Coverage MCP](https://github.com/appunni-m/coverage-mcp). Coverage MCP is a
Rust executable; the marketplace does not pretend that the Rust repository is
a Python package and does not invoke it through `uvx` or `pip`.

For local development from a Coverage MCP checkout, use Cargo directly. This
incrementally compiles the current source and avoids a separate local install:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

The first invocation may compile bundled DuckDB. Warm it before opening the
MCP client when the host has a short startup timeout:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

To make the local Codex registration use that launcher explicitly:

```bash
codex mcp remove coverage-mcp
codex mcp add coverage-mcp -- cargo run --locked \
  --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

For a host that is not running from the checkout or does not have Cargo, install
the binary once:

```bash
cargo install --git https://github.com/appunni-m/coverage-mcp.git \
  --locked coverage-mcp
coverage-mcp --version
```

The portable plugin connector runs `coverage-mcp connect` in the MCP client's
repository working directory. Add `--repo /absolute/path/to/repository` when
the host does not set that working directory. The connector is a direct stdio
process: it opens `<repo>/.coverage-mcp/coverage.duckdb` and does not start an
HTTP daemon.

The published manifest intentionally keeps this native default: it cannot
safely infer a user's Coverage MCP checkout. The machine-readable
`compatibility.json.localDevelopment` entry and the explicit Codex/Pi commands
above require the checkout path instead of silently guessing one.

Run the same connector manually with:

```bash
coverage-mcp connect --repo /absolute/path/to/repository
```

Verify the stdio handshake before opening an MCP client:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  | cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
      -- connect --repo /absolute/path/to/repository
```

The first response must contain `result.serverInfo.name` equal to
`coverage-mcp`. If the MCP client reports `connection closed: initialize
response`, inspect the command's stderr: the child exited before the
handshake, usually because the host is still configured with `uvx`, `pip`, a
missing Cargo manifest, missing native binary, or a locked database.

For local HTTP and dashboard use, start a separate loopback daemon through
Cargo:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- serve
curl http://127.0.0.1:59471/health
```

Dashboard:

```text
http://localhost:59471/
```

The dashboard is available only when the separate `serve` process is running. Agents
may remind users to open it after a managed test or coverage task reaches a
terminal state; they must not open it automatically.

Standalone stdio mode opens one database per selected Git root. Every linked
worktree reuses its repository database at:

```text
<shared-git-root>/.coverage-mcp/coverage.duckdb
```

Coverage MCP resolves the shared Git root so worktree runs retain one baseline
lineage. Do not point two processes at the same database at once; the database
lease will reject the second opener.

### What The Plugin Installs

Installing `testing@codegen-marketplace` copies the testing plugin into the
agent's user-level plugin cache. It provides:

- the `use-coverage-mcp` skill
- the `run-coverage-campaign` skill for Luna Max execution with Sol High strategy
- a stdio MCP connector backed by the native `coverage-mcp` executable
- agent prompts and plugin documentation

The plugin does not install Cargo, the Rust binary, or copy a DuckDB. For local
checkout development, configure the explicit Cargo launcher above. For a
portable installation, install `coverage-mcp` separately and keep the
executable on the MCP host's `PATH`, or configure its absolute path.

### Updating

Update the plugin when its skill, prompts, or MCP connection changes:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Start a new Codex thread after a plugin update.

For local source changes, restart the Cargo-launched connector; no build or
install step is required. Update an installed server when Coverage MCP
parsing, storage, API, dashboard, or performance code changes:

```bash
cargo install --git https://github.com/appunni-m/coverage-mcp.git \
  --locked --force coverage-mcp
```

Restart agent connectors after updating. Each repository's
`.coverage-mcp/coverage.duckdb` remains in place and is reopened by the new
native process.

Verify a local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

If an HTTP daemon is also in use, restart it and verify `/health` so its tool
inventory matches the updated Coverage MCP binary.

### Approved Test Runs

Coverage MCP does not read a YAML suite file. A human approves the exact command,
working directory, and expected artifacts before registration:

```text
register_test_command(
  name="unit",
  command="pytest --cov=src --cov-report=json",
  cwd="/path/to/repository",
  artifact_paths={
    "coveragepy": {
      "path": "coverage.json",
      "required": true,
      "coverage_format": "coveragepy",
      "suite": "unit"
    }
  },
  human_approved=true,
  approved_by="maintainer",
  approval_note="approved unit coverage command"
)
```

Agents then run only the registered id or name:

```text
run_test(
  command_ref="unit",
  idempotency_key="unit:<commit-sha>:requested-check",
  max_words=500
)
```

The call returns a durable run id immediately. Fetch it with `get_run_data` no
faster than the returned `poll_after_ms`; wait that long after each
non-terminal response before fetching again. Retries for the same intended run
must reuse the same idempotency key:

```text
get_run_data(run_id="returned-run-id", detailed=false, max_words=500)
```

Once the approved command has completion history, run data responses report a
median ETA, p90 duration, sample count, estimated start/completion times, and
queue wait.
Queue wait models the server's worker lanes. If a required duration has no
usable history, the server returns a null ETA with an explicit reason instead
of guessing.

The compact final result contains the important status, counters, freshness,
artifact, and ingestion fields. Pass `detailed=true` only when full run
metadata is required. Detailed results still omit embedded stdout/stderr.
Search retained logs only when needed:

```text
search_test_logs(
  run_id="returned-run-id",
  query=["FAILED", "timeout"],
  context_lines=5,
  max_words=400
)
```

`query` may be one literal string or a list of literal strings. `max_words` is
the response budget; `context_lines` only controls which nearby lines are
considered relevant.

Inspect one file without loading every coverage record:

```text
coverage_query(
  view="file",
  snapshot_id="...",
  file_path="src/example.py",
  line_ranges=[{"start": 10, "end": 20}, {"start": 80, "end": 95}]
)
```

The default response groups coverage gaps. `line_ranges` is optional and
returns compact exact covered/uncovered records from up to 10 windows and 200
unique lines. Duplicate, nested, overlapping, adjacent, and unordered windows
are normalized before the budget is applied.

Use `cancel_run(run_id, detailed=false)` to cancel obsolete queued or running
work. Running cancellation and timeouts terminate the command's complete
process group.

Run retention is count-based per approved command: the newest 100 terminal runs
are kept by default. Configure the server with `COVERAGE_MCP_RUN_RETENTION` to
change the limit; coverage snapshots and registered artifacts are unaffected.

Artifacts declaring `coverage_format` are automatically ingested only when the
managed run creates or modifies them. Read `coverage_ingest.status` and use the
returned snapshot ID directly:

```text
coverage_query(view="insights", snapshot_id="...", detailed=false)
coverage_compare(view="progress", worktree_id="...", suite="unit", detailed=false)
```

Reserve `ingest_coverage` for external or historical reports not produced by a
managed registered command. A `not_recorded` result identifies a pre-0.3.3 run
with no automatic-ingestion decision; do not infer or create a snapshot from
its potentially stale artifact.

### Agent Policy

Projects can add this to `AGENTS.md`:

```md
## Coverage MCP

- Reuse the repository's single Coverage MCP server and shared DuckDB. Never
  create or copy a worktree-local database.
- Run tests only through a registered, human-approved command. Ask for explicit
  approval of the full command, cwd, and artifact paths before registration.
- Give each intended run a stable idempotency key. Keep the returned run id,
  fetch `get_run_data(detailed=false)` no sooner than `poll_after_ms`, and
  reuse the key for every retry.
- Register each linked worktree once before its first coverage run and retain
  its `worktree_id`.
- Declare managed reports with `coverage_format` and a stable suite. Use the
  snapshot ID from terminal `coverage_ingest`; do not ingest it twice.
- Use `ingest_coverage` only for reports produced outside the managed runner.
- Compare worktree progress only with its frozen suite-specific baseline.
- Query summaries, insights, files, and exact lines before reading source or
  raw coverage artifacts.
```

## Development

```bash
pnpm install
pnpm build
pnpm check
```

`pnpm check` validates marketplace schemas, every Agent Skill, local
documentation links, cross-target manifest consistency, and the Pi installer.
CI also rebuilds the marketplace and rejects stale generated artifacts.

Authored plugin sources live under `plugins/`. Repository-root host artifacts,
registries, `skills/`, and `dist/` are generated by `aipm build`; do not edit
them directly.

```text
.
├── aipm.workspace.ts
├── plugins/
│   ├── rust-development/
│   │   ├── aipm.config.ts
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .cursor-plugin/plugin.json
│   │   └── skills/
│   └── testing/
│       ├── aipm.config.ts
│       ├── .claude-plugin/plugin.json
│       ├── .codex-plugin/plugin.json
│       ├── scripts/install-pi-mcp.mjs
│       └── skills/use-coverage-mcp/
├── skills/                         # generated
├── dist/                           # generated
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
└── .cursor-plugin/marketplace.json
```

Gemini and Kiro are single-artifact hosts. Only one plugin may claim each of
those targets. Claude Code, Codex, and Cursor use generated registries and can
expose multiple plugins.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the authoring and release checks.

## Credits

- Marketplace scaffolding is derived from
  [Mike North's AI Plugin Marketplace Template](https://github.com/mike-north/ai-plugin-marketplace-template).
- The core Rust development guidance is adapted from
  [Apollo GraphQL's agent skills](https://github.com/apollographql/skills).
- The Rust coding-guidelines skill adapts selected guidance from
  [Leonardo Maldonado's rust-skills](https://github.com/leonardomso/rust-skills).
- Complete copyright and license texts are preserved in
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

MIT. See [LICENSE](LICENSE). Third-party material and its preserved license
notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
