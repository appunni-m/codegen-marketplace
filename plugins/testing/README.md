# Testing

Testing workflows backed by the local
[Coverage MCP](https://github.com/appunni-m/coverage-mcp) server.

Coverage MCP is a native Rust executable. Codex declares it as a required
stdio server in the bundled `.mcp.json`. The configuration checks `PATH` for
exact `coverage-mcp 0.13.0`, otherwise checks
`~/.coverage-mcp/runtime/0.13.0`. On a cache miss it downloads the matching
checksummed GitHub Release archive for macOS or Linux on ARM64 or x86-64,
verifies the extracted version, atomically fills the cache, and immediately
executes `coverage-mcp connect`. There is no plugin-owned launcher file, custom
installer lock, direct HTTP client, or database fallback.

Supported targets need POSIX `sh`, `curl`, `tar`, and either `sha256sum` or
`shasum`; they do not need Rust and do not compile bundled DuckDB. If a native
archive is unavailable or cannot run on the host, an existing Cargo toolchain
provides an exact-version fallback. Stable Cargo has no registry command
equivalent to “download this crate and run its binary”. For checkout-local
development, use `cargo run --package coverage-mcp -- connect`; the `.mcp.json`
bootstrap handles exact binary acquisition only and never follows an unpinned
Git branch. Set `COVERAGE_MCP_RUNTIME_DIR` to relocate the cache. The
900-second timeout exists for the slow Cargo fallback; prebuilt and cached
starts do not compile.

The bundled bootstrap is POSIX `sh` and supports macOS, Linux, and WSL. Native
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
cargo install coverage-mcp --version '=0.13.0' --locked
coverage-mcp --version
```

The bootstrap preserves the MCP client's repository working directory and
replaces itself with `coverage-mcp connect`. From that point, `connect` owns
the complete runtime lifecycle: repository selection, fixed-port discovery,
stale-state recovery, version handoff, daemon startup, and stdio forwarding on
`127.0.0.1:59471`. Only the daemon process holds its ownership lease; stdio
bridges and direct HTTP clients do not lock one another. The daemon remains
available after an individual connector exits. Use an explicit
`--repo` for native host configurations that do not provide a repository
working directory. The bundled connector is in `.mcp.json`, and the
machine-readable bootstrap/runtime contract is in `compatibility.json`. The
server must report schema revision 14, eight public tools, and
`tools/list.contract.tools_sha256=3dd1da08e6bf7053e8e64cf310dc9c328488413754a42fe3060ef3afef09f892`.
The eighth tool, `find_duplicate_coverage_tests`, returns bounded groups of
named tests with exactly equal normalized line, branch, and function
observation sets. It is a coverage-equivalence candidate signal only: it does
not compare test logic and never authorizes deletion. Its defaults are the
latest snapshot, ten groups, and ten test names per group; continue with the
opaque `page.next_cursor` when more groups are needed.

The stdio process can outlive a daemon crash. If the next connection is
refused, that same bridge uses the released OS lease and its leftover metadata
file to start one replacement daemon, then replays the request once because it
was never delivered. A timeout or other ambiguous failure triggers health
recovery for later calls without replaying a potentially committed write. No
operator deletes a lock and no connection lock is added.

A newer connector automatically replaces an older daemon after verifying that
its loopback health and actively held `daemon.lock` identify the same process,
executable, common database, and instance. New daemons use a
capability-authenticated graceful handoff; the first upgrade from a
pre-handoff daemon uses its verified lease PID. Unknown listeners, different common
databases, equal-version incompatibilities, and downgrade attempts fail closed.
No client lock is introduced: HTTP and stdio connections remain concurrent.

When an ungraceful daemon exit leaves durable run state behind, the replacement
daemon reconciles it as each project store opens. A formerly `running` command
becomes terminal `interrupted` and is not replayed; a command that was still
`queued` resumes through the normal worker limit. Agents can continue polling
the same run IDs, and no database edit or connector reload is required.

The published Codex manifest keeps the runtime version pinned because an
installed plugin cannot safely infer a user's Coverage MCP checkout or track a
moving Git branch. Use the explicit Cargo manifest option for local
development; it never falls back to a guessed path. Do not publish this plugin
version until Coverage MCP 0.13.0 exists on crates.io and all four claimed
native archives, `SHA256SUMS`, and provenance are published.
This plugin revision is synchronized with Coverage MCP schema revision 14 and
its eight-tool public inventory; verify those values through `GET /health` and
`tools/list` after upgrading.

```bash
coverage-mcp connect --repo /absolute/path/to/repository
~/.coverage-mcp/runtime/0.13.0/bin/coverage-mcp connect \
  --repo /absolute/path/to/repository
```

## Incremental runs without re-registering commands

Register one human-approved command that safely accepts the intended runtime
arguments, for example `cargo test -- {{args}}` when that exact command and
filter boundary have been approved. Reuse the returned command ID or name for
every case; do not register a new command for each test filter.

Pass the case-specific arguments and an explicit fixed-base snapshot to
`run_test`:

```json
{
  "command_ref": "coverage-tests",
  "arguments": ["--filter", "parser::handles_empty_input"],
  "execution": {"mode": "incremental", "label": "parser empty input"},
  "baseline": {"kind": "explicit", "snapshot_id": "<base_snapshot_id>"},
  "reuse_if_unchanged": true,
  "idempotency_key": "parser-empty-input-v1"
}
```

The server shell-quotes each argument and replaces the command's single
`{{args}}` placeholder, or appends the quoted arguments when no placeholder is
present. `execution.identity` is optional: the server persists a fingerprint
of mode, arguments, and baseline, so different cases cannot accidentally reuse
one another. Use a different idempotency key for each materially different
case.

Obtain `base_snapshot_id` from a completed full run's
`data.coverage_ingest.snapshot_ids[0]` or a compatible `coverage_import`
result. The server never guesses the latest or previous snapshot. After the
incremental run reaches terminal state and ingests exactly one current report,
the run response and `run_review(view="status")` contain
`incremental_review` automatically. A pending or not-measured status is not a
coverage claim; report its server-provided reason.

Use `coverage_review(task="incremental")` only to compare two snapshots that
already exist independently of a run. It reads stored detail, never reruns
tests or reparses the baseline, and requires
`measurement.snapshot_id` (or an unambiguous run) plus
`baseline.kind="explicit"` and `baseline.snapshot_id`.

Compaction does not change snapshot IDs and incremental comparison can read
compacted detail; inspect `incremental.detail_source` to see whether each side
came from relational rows or a compacted payload. Mark a long-lived fixed base
artifact `detail_retention=incremental_base` when it must be excluded from
ordinary compaction. Reports without named test observations expose an
explicit unavailable attribution status rather than invented test identities.

## Composite production coverage

Coverage MCP schema 14 lets one managed run produce a single authoritative
production-coverage view across Rust/WGSL, Python, and JavaScript. Register the
command once with one required inventory artifact and one required descriptor
for every component/package variant. Full and incremental runs use that same
registration; pass only the approved case-specific `arguments`, execution
metadata, and explicit baseline for the case.

Each coverage descriptor declares its mapping rather than relying on filenames:

```json
{
  "path": "target/python.json",
  "required": true,
  "coverage_format": "coveragepy",
  "composite": {
    "component_id": "python",
    "package_variant": "cpython",
    "language": "python",
    "format": "coveragepy",
    "inventory_artifact": "target/inventory.json",
    "role": "coverage",
    "logical_source_aliases": [
      {"path": "pkg/runtime.py", "logical_source_id": "python:pkg/runtime.py"}
    ],
    "toolchain_versions": {"coverage.py": "7.x"}
  }
}
```

The inventory is authoritative for the canonical-region denominator. Logical
source aliases are the only deduplication mechanism; matching paths, packages,
bytes, or filenames never merge regions. Every declared variant must be
present, fresh, well-formed, and source-compatible. Missing, stale, malformed,
or source-mismatched evidence leaves the composite `incomplete` and never
reduces its denominator.

Save `data.composite_snapshot_id` from every completed composite run. For a
smaller composite case, use the same incremental `run_test` shape but provide
`baseline.kind="explicit"` and `baseline.composite_snapshot_id`. The terminal
run automatically exposes its bounded `incremental_review`; standalone
`coverage_review(task="incremental")` is only for comparing two already stored
composite snapshots. Composite incremental review reads stored canonical-region
rows and child named-test observations, never reruns the fixed base, and
requires matching repository, mapping version, and inventory hash.

Compaction does not rewrite composite rows. If ordinary child snapshots were
compacted, the server restores their detail from the zstd payload for comparison
and reports the detail source. Keep a long-lived base's artifacts at
`detail_retention="incremental_base"` when avoiding restoration work matters;
named-test attribution remains explicitly `unavailable` for formats without
named observations.

## Installation Boundary

The testing plugin installs the `coverage-review` workflow skill, an exact-binary
release bootstrap, and the required stdio connector. Concurrent downloads use
isolated temporary directories and atomically install the same verified bytes;
the Cargo fallback also accepts a racing exact binary. The plugin introduces no
second lifecycle lock. Normal `connect` processes are lightweight bridges;
they do not open DuckDB or take the daemon ownership lease. The first bridge
starts the daemon, whose process alone holds `<common-db-parent>/daemon.lock`
while listening on the fixed default port `59471`. Any number of HTTP clients
and stdio bridges may connect concurrently, subject to configured runtime
limits. The daemon lazily opens the selected repository's
`.coverage-mcp/coverage.duckdb`, so multiple projects can connect concurrently
without becoming competing database owners. Connector and compaction processes
always route through the daemon and never open project databases themselves.

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
skills and bundled MCP connector. Plugin discovery occurs when Codex creates a
task; after the connector is present, shared-daemon crash recovery stays within
the existing task.

Published upgrades no longer require manually stopping the existing daemon; the
newer connector performs the verified handoff. A same-version local rebuild is
not an upgrade, so stop that development daemon or change the checkout version
before reconnecting. Update a manually installed native binary separately
after a published release:

```bash
cargo install coverage-mcp --version '=0.13.0' --locked --force
```

Start a new Codex task after reinstalling the plugin. Its connector resolves the
updated executable, replaces the verified older daemon, and preserves each
repository's `.coverage-mcp/coverage.duckdb` history.

Verify the local checkout launcher:

```bash
cargo run --locked --manifest-path /absolute/path/to/coverage-mcp/Cargo.toml \
  -- --version
```

After `connect` has started, use `curl http://127.0.0.1:59471/health`. The
reported version and instance ID should match the updated connector after its
automatic handoff.

After a test or coverage task completes, the managed dashboard is available at
<http://localhost:59471/>; do not open the browser automatically.

Register test commands only after a human approves the complete command,
working directory, and artifact paths. The full approval, execution, polling,
freshness, lineage, response-budget, and reporting contract lives in the
[`coverage-review` skill](skills/coverage-review/SKILL.md); it is intentionally
not duplicated in this integration README.

Use [`run-coverage-campaign`](skills/run-coverage-campaign/SKILL.md) only for
input-driven campaign work. It composes `coverage-review` and owns only its
campaign-specific batching and model-routing rules. Coverage MCP remains the
source of truth for tool schemas, validation, response shapes, and bounded
projections. Raw LLVM/LCOV inspection remains valid for an independent narrow
check, while managed reviews add lineage, freshness, provenance, and history
normalization.

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
