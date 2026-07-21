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
| `testing` | Human-approved test runs, bounded summaries, coverage history, exact missing lines, and worktree baseline comparisons | Claude Code, Codex, Gemini CLI (combined extension), Pi |

## Install

Install only the plugins needed for a given agent.

### Codex

```bash
codex plugin marketplace add appunni-m/codegen-marketplace
codex plugin add rust-development@codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Start a new Codex thread after installation.

### Claude Code

```bash
claude plugin marketplace add appunni-m/codegen-marketplace
claude plugin install rust-development@codegen-marketplace
claude plugin install testing@codegen-marketplace
```

Start a new Claude Code session after installation.

### Cursor

Import the marketplace repository in **Settings > Plugins**:

```text
https://github.com/appunni-m/codegen-marketplace
```

The Cursor target currently contains `rust-development`.

### Gemini CLI

```bash
gemini extensions install https://github.com/appunni-m/codegen-marketplace
```

Gemini has one repository-level extension slot, owned by `rust-development`.
The combined extension also configures Coverage MCP through `uvx`, so installing
the repository provides both Rust guidance and testing/coverage tools. Restart
Gemini CLI after installation or update.

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
```

The testing plugin also needs Pi's MCP adapter because Pi does not expose MCP as
a native marketplace target:

```bash
pi install npm:pi-mcp-adapter
node ./codegen-marketplace/plugins/testing/scripts/install-pi-mcp.mjs
```

Restart Pi after installing the adapter.

## Coverage MCP

The `testing` plugin launches a stdio connector for
[Coverage MCP](https://github.com/appunni-m/coverage-mcp). The connector uses
the public HTTPS Git repository and starts or reuses one user-level HTTP daemon.
It deliberately tracks upstream `main`; this is declared in
`plugins/testing/compatibility.json` and checked by the marketplace tests.

Run the same connector manually with:

```bash
uvx --from git+https://github.com/appunni-m/coverage-mcp.git@main \
  coverage-mcp connect
```

Python 3.12 or newer is required. Verify the server:

```bash
curl http://127.0.0.1:59471/health
```

The response must include `version`; `common_db_path` must identify the daemon's
common registry, and `run_concurrency` reports the active worker count.

Dashboard:

```text
http://localhost:59471/
```

Agents remind users to open this dashboard in a browser after a managed test or
coverage task reaches a terminal state.

One daemon serves every repository and lazily opens one database per shared Git
root. Every linked worktree reuses its repository database at:

```text
<shared-git-root>/.coverage-mcp/coverage.duckdb
```

Do not start a daemon per repository or worktree. Coverage MCP resolves the
shared Git root so worktree runs retain one baseline lineage.

### What The Plugin Installs

Installing `testing@codegen-marketplace` copies the testing plugin into the
agent's user-level plugin cache. It provides:

- the `use-coverage-mcp` skill
- a stdio MCP connector backed by `uvx` and the public HTTPS Git repository
- agent prompts and plugin documentation

`uvx` installs or updates the isolated Python package as needed, and the
connector starts the daemon on demand. The plugin never copies a DuckDB.

### Updating

Update the plugin when its skill, prompts, or MCP connection changes:

```bash
codex plugin marketplace upgrade codegen-marketplace
codex plugin add testing@codegen-marketplace
```

Start a new Codex thread after a plugin update.

Update the server when Coverage MCP parsing, storage, API, dashboard, or
performance code changes:

```bash
python -m pip install --upgrade \
  "coverage-mcp @ git+https://github.com/appunni-m/coverage-mcp.git@main"
```

Restart agent connectors after updating. Each repository's
`.coverage-mcp/coverage.duckdb` remains in place and is reopened lazily.

Verify the running package version and common registry path:

```bash
curl http://127.0.0.1:59471/health
```

Restart connectors after upstream changes so their tool inventory matches
Coverage MCP `main`.

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
