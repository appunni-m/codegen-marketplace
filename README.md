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
| `rust-development` | Rust implementation, debugging, documentation, crate research and releases, coding standards, and unsafe review | Claude Code, Codex, Cursor, Gemini CLI, Kiro, Vercel Skills CLI, Pi |
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

The schema-9 contract is summarized in the
[Coverage MCP contract pointer](docs/coverage-mcp-contract.md). The canonical
server exposes seven task-oriented public tools and enforces the same typed
contract across HTTP and stdio.

The `testing` plugin launches a native stdio connector for
[Coverage MCP](https://github.com/appunni-m/coverage-mcp). Coverage MCP is a
Rust executable; the marketplace does not pretend that the Rust repository is
a Python package and does not invoke it through `uvx`, `pip`, Node, or `npx`.

### Automatic Codex bootstrap

Codex loads a required stdio declaration from the testing plugin's `.mcp.json`.
The configuration checks `PATH` for exact `coverage-mcp 0.10.0`, then the
versioned cache at `~/.coverage-mcp/runtime/0.10.0`. On a cache miss it maps the
host to one of four native GitHub Release archives:

| Host | Release target |
| --- | --- |
| Apple Silicon macOS | `aarch64-apple-darwin` |
| Intel macOS | `x86_64-apple-darwin` |
| ARM64 Linux/WSL | `aarch64-unknown-linux-gnu` |
| x86-64 Linux/WSL | `x86_64-unknown-linux-gnu` |

The POSIX bootstrap downloads the exact archive and `SHA256SUMS`, fails closed
on an integrity mismatch, verifies the extracted binary reports 0.10.0, and
atomically fills the cache. Supported targets therefore need no Rust toolchain
and do not compile DuckDB. If the host is unsupported or GitHub is unavailable,
an existing Cargo toolchain provides a slower exact-version fallback.

The bootstrap immediately replaces itself with `coverage-mcp connect`. It has
no standalone launcher file, custom installer lock, daemon logic, HTTP
fallback, or database access. Concurrent acquisitions use isolated temporary
directories and may atomically install the same verified bytes; they never lock
client connections. At runtime, `connect` alone owns repository routing,
fixed-port discovery, daemon startup, stale-state recovery, and version
handoff. The daemon alone holds its process-ownership lease while listening on
port `59471`; neither stdio bridges nor direct HTTP clients take that lease.
Both transports can create concurrent connections, subject to daemon resource
limits. The 900-second startup timeout is retained only for the Cargo fallback;
cached and prebuilt starts do not compile.

If the pinned connector is newer than the daemon already using port `59471`,
`connect` verifies that `/health` and the actively held `daemon.lock` identify
the same Coverage MCP process and common database. It then requests an
authenticated graceful handoff and starts the pinned binary after the existing
listener and lease are released. The first upgrade from a pre-handoff daemon
uses its verified PID/executable lease metadata. Unknown listeners,
different registries, equal-version incompatibilities, and attempts to
downgrade a newer daemon are refused; the connector never deletes lock, WAL, or
database files.

This provides the first-install behavior users expect from `uvx` or `npx`.
Stable Cargo has no registry command that downloads and runs an arbitrary crate
binary. For checkout-local development, use `cargo run --package coverage-mcp --
connect`; the MCP bootstrap performs only exact executable acquisition and does
not install Rust itself. Set
`COVERAGE_MCP_RUNTIME_DIR` to relocate the versioned cache. A marketplace
release must not reference a Coverage MCP version until its crate, four native
archives, checksums, and provenance are published.

The bundled bootstrap is POSIX `sh` and is intended for macOS, Linux, and WSL.
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
cargo install coverage-mcp --version '=0.10.0' --locked
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

An already-running stdio bridge also recovers a crashed daemon. When TCP
refuses the next request, the bridge reuses the now-unlocked stale lease file,
starts one replacement daemon, and replays that provably undelivered request
once. It restores daemon health after ambiguous transport failures without
replaying a write whose commit status is unknown. This recovery creates no
client lock; concurrent HTTP and stdio connections remain independent.

When the replacement daemon reopens a project, it terminalizes orphaned
`running` jobs as `interrupted` without replaying their commands and restarts
jobs that remained `queued` through the normal worker limit. The same run IDs
remain queryable, so stale active state heals without direct database access.

The published Codex `.mcp.json` contains the plugin-bundled bootstrap; it does not
guess a Coverage MCP checkout. The machine-readable
`compatibility.json.localDevelopment` entry and the explicit local-development
command above require a checkout path. Gemini, Claude, and Pi retain their
documented native command and therefore need `coverage-mcp` on `PATH` or an
explicit Cargo/absolute-path registration.
At this marketplace revision, the synchronized Coverage MCP contract is schema
revision 9 with seven public tools. The server's `tools/list.contract.tools_sha256`
must equal
`28fb24dbcc43910e3592d8e4f4c35057acb97e731ceb8a274a2dc96e0b016b16`;
`GET /health` and `tools/list` remain the runtime authorities.

Run a PATH installation manually, or invoke the Codex-managed cache directly:

```bash
coverage-mcp connect --repo /absolute/path/to/repository
~/.coverage-mcp/runtime/0.10.0/bin/coverage-mcp connect \
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
the bootstrap cannot download or verify its pinned release and no Cargo
fallback exists, a local Cargo manifest is missing, automatic daemon handoff refused an
unverified/equal/newer owner, or another daemon or external
process still owns the selected database.

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
becoming competing database owners. Every connector and compaction request goes
through that daemon; client processes never open project databases.

### What The Plugin Installs

Installing `testing@codegen-marketplace` copies the testing plugin into the
agent's user-level plugin cache. It provides:

- the `coverage-review` workflow skill for managed test and coverage review
- the `run-coverage-campaign` skill for Luna Max execution with Sol High strategy
- a required Codex stdio declaration whose inline bootstrap downloads and
  verifies one pinned native binary, then executes `connect`
- agent prompts and plugin documentation

The plugin does not install Cargo or a separate DuckDB library. The release
binary already contains bundled DuckDB; Cargo is used only as a fallback. For
local checkout development, configure the explicit Cargo launcher above. Other
hosts must keep `coverage-mcp` on `PATH` or configure an absolute path.

### Updating

Update the plugin when its skill, prompts, or MCP connection changes:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Start a new Codex task after a plugin update so it loads the refreshed skills
and MCP connector. Codex discovers newly installed plugin tools when a task is
created; once its stdio connector is loaded, daemon crash recovery happens
inside that same task without a connector reload.

Published Coverage MCP upgrades no longer require manually stopping the existing
daemon: the newer connector performs the verified handoff automatically. A
same-version local rebuild is intentionally not treated as an upgrade; stop
that development daemon or change the checkout version before reconnecting.
The portable Codex connector changes runtime versions only when the plugin's
pinned version changes. To update a manually installed server after a
published Coverage MCP release:

```bash
cargo install coverage-mcp --version '=0.10.0' --locked --force
```

Start a new Codex task after updating the plugin so Codex launches the refreshed
stdio connector. That connector replaces the verified older daemon and reopens
each repository's existing `.coverage-mcp/coverage.duckdb` in the new process.

Verify a local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

Start a new MCP session and verify `/health` so the automatically managed
daemon's tool inventory matches the updated Coverage MCP binary.

### Coverage workflow

The [`coverage-review` skill](plugins/testing/skills/coverage-review/SKILL.md)
is the single home for approval, polling, freshness, lineage, response-budget,
and reporting policy. Keep this README focused on installation and integration;
use the canonical Coverage MCP README for the server's wire contract and the
skill for the agent workflow.

The [`run-coverage-campaign` skill](plugins/testing/skills/run-coverage-campaign/SKILL.md)
adds campaign-specific batching and model-routing rules. It composes
`coverage-review` rather than redefining its evidence policy.

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
│       └── skills/coverage-review/
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
