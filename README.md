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
| `testing` | Coverage gap queries and report comparisons | Claude Code, Codex, Gemini CLI (combined extension), Pi |
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

The testing plugin exposes two read-only tools: `coverage_gaps` finds a few exact
source locations; `coverage_compare` explains changes between explicit reports.
Inspect code with `rg` and run the existing repository test command. Reports need
no import. There is no managed command registration, run polling, source paging,
or required model routing.

### Runtime and installation

Install `testing@codegen-marketplace` through the client's plugin interface.
The Codex connector inherits the project directory and executes
`coverage-mcp connect`. It accepts the exact pinned binary on PATH, otherwise
acquires a native release using checksum verification and a locked Cargo
fallback. The bootstrap only obtains the binary; daemon ownership and recovery
belong to Coverage MCP. Native archives support macOS, Linux, and WSL; native
Windows is not claimed.

The plugin pins **Coverage MCP 0.16.0**, schema revision 18.
For local runtime development, use `cargo install --path . --locked` from the
Coverage MCP checkout, or a contributor launcher:

```sh
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- connect --repo /absolute/path/to/repository
```

Gemini and Pi use the native binary on PATH. The [testing integration guide](plugins/testing/README.md)
and [compatibility metadata](plugins/testing/compatibility.json) describe the
connector. The plugin does not install Cargo or a separate DuckDB library.

The first connector starts or reuses one shared daemon on `127.0.0.1:59471`.
The daemon survives connector exit and routes repositories to their own stored
history; do not start one daemon per project. Existing snapshots and compacted
detail remain readable. The health endpoint is `/health` and the optional
dashboard is <http://127.0.0.1:59471/>. Standalone report-file `gaps` and `compare`
commands do not require the daemon or a database.

To measure only new tests against an existing baseline, use `coverage_compare`
with `scope: "incremental"`. The result shows added coverage and the combined
total; optional `previous` includes earlier batches. Run selected tests with the
repository runner. See the [testing integration guide](plugins/testing/README.md).

### Connector updates

After updating the plugin and matching runtime, start a new task so the client
loads the new tool definitions. Verify `/health` and `pnpm check:coverage-mcp`
during local development. See the [contract pointer](docs/coverage-mcp-contract.md)
for the server documentation.

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
│       └── .mcp.json
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
