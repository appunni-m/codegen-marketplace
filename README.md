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

Start a new Codex task after installation.

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
a Python package and does not invoke it through `uvx`, `pip`, Node, or `npx`.

### Automatic Codex bootstrap

Codex runs the plugin-relative `./bin/coverage-mcp-launcher`. It first honors
an exact `COVERAGE_MCP_BIN`, then checks `PATH`, then checks the versioned cache
at `~/.coverage-mcp/runtime/0.8.0`. If no exact Coverage MCP 0.8.0 binary is
available, one launcher acquires
`~/.coverage-mcp/runtime/.install-0.8.0.lock` and runs:

```bash
cargo install coverage-mcp --version '=0.8.0' --locked \
  --bin coverage-mcp --root <temporary-install-root>
```

The completed installation is moved into the versioned cache, waiting Codex
sessions reuse it, and every launcher then executes `coverage-mcp connect`.
The install lock is released before any connector starts. At runtime the daemon
alone holds its process-ownership lease while listening on port `59471`;
neither stdio bridges nor direct HTTP clients take that lease. Both transports
can create concurrent connections to the same daemon, subject only to its
configured request and connection-pool limits. The MCP declaration allows 900
seconds for the first compile; cached starts do not rebuild.

This is the Cargo analogue of `uvx` or `npx`: automatic and version-pinned, but
it requires an existing Rust/Cargo toolchain just as `npx` requires Node. It
does not install Rust itself. Set `COVERAGE_MCP_RUNTIME_DIR` to relocate the
versioned cache. `COVERAGE_MCP_BOOTSTRAP_TIMEOUT_SECONDS` changes the default
900-second wait for another first-session install; keep the MCP host's startup
timeout at least as large. A marketplace release must not reference a Coverage MCP
version until that exact crate is published on crates.io; otherwise the
launcher fails with a release-prerequisite error instead of installing moving
Git source.

The bundled launcher is POSIX `sh` and is intended for macOS, Linux, and WSL.
Native Windows bootstrap is not currently claimed; install the pinned crate
manually, disable the bundled server, and register the absolute
`coverage-mcp.exe connect` command with the MCP host.

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

When the testing plugin is enabled, its bundled server and a global
`codex mcp` registration are separate entries. Disable the bundled server in
`~/.codex/config.toml` before adding a checkout-local global connector:

```toml
[plugins."testing".mcp_servers.coverage-mcp]
enabled = false
```

Then register the Cargo launcher:

```bash
codex mcp remove coverage-mcp
codex mcp add coverage-mcp -- cargo run --locked \
  --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

Remove that global registration and re-enable the bundled server when returning
to the installed binary. This avoids loading duplicate Coverage MCP tool sets.

For a non-Codex host, or to prewarm the binary before the first Codex task,
install the published version explicitly:

```bash
cargo install coverage-mcp --version '=0.8.0' --locked
coverage-mcp --version
```

The Codex bootstrap ultimately runs `coverage-mcp connect` in the MCP client's
repository working directory. Other host connectors invoke that native command
directly. Add `--repo /absolute/path/to/repository` when a host does not set the
repository working directory. The connector is a lightweight stdio bridge that
starts or reuses the HTTP daemon at `127.0.0.1:59471`; the daemon alone holds
the ownership lease that prevents a duplicate daemon process. HTTP clients and
stdio bridges do not lock one another. The daemon opens
each selected repository's `<repo>/.coverage-mcp/coverage.duckdb` lazily and
remains available when an individual bridge exits.

The published Codex `.mcp.json` uses the plugin-relative bootstrap; it does not
guess a Coverage MCP checkout. The machine-readable
`compatibility.json.localDevelopment` entry and the explicit local-development
command above require a checkout path. Gemini, Claude, and Pi retain their
documented native command and therefore need `coverage-mcp` on `PATH` or an
explicit Cargo/absolute-path registration.
At this marketplace revision, the synchronized Coverage MCP contract is schema
revision 7 with eleven tools; `GET /health` and `tools/list` are the runtime
authorities.

Run a PATH installation manually, or invoke the Codex-managed cache directly:

```bash
coverage-mcp connect --repo /absolute/path/to/repository
~/.coverage-mcp/runtime/0.8.0/bin/coverage-mcp connect \
  --repo /absolute/path/to/repository
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
handshake, usually because the host is still configured with `uvx` or `pip`,
the bootstrap cannot find Cargo or its pinned published crate, a local Cargo
manifest is missing, `COVERAGE_MCP_BIN` has the wrong version, the daemon is
incompatible, or a standalone process still owns the selected database.

The connector starts the loopback daemon automatically. You can still run it
explicitly through Cargo while developing the server:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- serve
curl http://127.0.0.1:59471/health
```

Dashboard:

```text
http://localhost:59471/
```

After `connect` starts, the dashboard is available from the managed daemon.
Agents may remind users to open it after a managed test or coverage task
reaches a terminal state; they must not open it automatically.

The shared daemon opens one database per selected Git root. Every linked
worktree reuses its repository database at:

```text
<shared-git-root>/.coverage-mcp/coverage.duckdb
```

Coverage MCP resolves the shared Git root so worktree runs retain one baseline
lineage. Concurrent connectors route through the same daemon instead of
becoming competing database owners. Supplying `connect --db` explicitly opts
into standalone stdio and must not target a database the daemon already owns.

### What The Plugin Installs

Installing `testing@codegen-marketplace` copies the testing plugin into the
agent's user-level plugin cache. It provides:

- the `use-coverage-mcp` skill
- the `run-coverage-campaign` skill for Luna Max execution with Sol High strategy
- a Codex stdio launcher that installs one pinned native binary with Cargo when
  necessary, then reuses it from a versioned cache
- agent prompts and plugin documentation

The plugin does not install Cargo and never copies a DuckDB. For Codex it can
install the published Rust binary automatically with the existing Cargo
toolchain. For local checkout development, configure the explicit Cargo
launcher above. Other hosts must keep `coverage-mcp` on `PATH` or configure an
absolute path.

### Updating

Update the plugin when its skill, prompts, or MCP connection changes:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Start a new Codex task after a plugin update so it loads the refreshed skills
and MCP connector.

For local source changes, stop the old Cargo-launched daemon; the next
connector starts the rebuilt checkout without an install step. The portable
Codex connector changes runtime versions only when the plugin's pinned version
changes. To update a manually installed server after a published Coverage MCP
release:

```bash
cargo install coverage-mcp --version '=0.8.0' --locked --force
```

Stop the old shared daemon after updating; the next agent connector starts the
new native process automatically. Each repository's
`.coverage-mcp/coverage.duckdb` remains in place and is reopened by the daemon.

Verify a local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

Start a new MCP session and verify `/health` so the automatically managed
daemon's tool inventory matches the updated Coverage MCP binary.

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

- Reuse the user-level Coverage MCP daemon and the canonical repository's
  `.coverage-mcp/coverage.duckdb`. Never start one daemon per project or create
  a database copy per agent or linked worktree.
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
