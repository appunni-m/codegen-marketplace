# Testing

A native Rust Coverage MCP connector with two read-only tools:
`coverage_gaps` locates missing coverage and `coverage_compare` compares reports.
Use the repository's test commands and ordinary source search such as `rg`.

## Install and runtime

Install `testing` from `codegen-marketplace` in Codex. The connector uses
`coverage-mcp connect`, inherits the client project directory, and starts or
reuses the shared daemon. HTTP and stdio use the same contract.

The plugin pins **Coverage MCP 0.16.0**, schema revision 18. For local runtime
development, install the tested checkout with `cargo install --path . --locked`
from Coverage MCP so the exact binary is on PATH. Contributor launcher alternative:

```sh
cargo run --locked --manifest-path ../coverage-mcp/Cargo.toml -- connect
```

The bootstrap first accepts the exact PATH binary, otherwise acquires the pinned
release with checksum verification and a locked Cargo fallback. It only obtains
the binary. Daemon ownership, upgrades, and recovery belong to Coverage MCP.
The daemon survives connector exit; do not start one daemon per project.

## Report queries

Tools accept report paths without an import. Existing saved snapshots can also
be selected by ID. Results contain exact source spans, evidence status, and
bounded detail in an envelope capped at 12 KiB. See the server reference for
inputs and comparison semantics.

Use `coverage_compare` with `scope: "incremental"` to measure a new batch against
a fixed baseline. Optional `previous` includes earlier accepted reports without
rerunning them. Results distinguish marginal gain, overlap, combined totals,
and unchecked full-suite regressions. The dashboard displays the same evidence.

The CLI offers the same `gaps` and `compare` reader without requiring an MCP
connection. Optional dashboard: <http://127.0.0.1:59471/>.

See [the contract pointer](../../docs/coverage-mcp-contract.md),
[compatibility metadata](compatibility.json), and the
[server reference](https://github.com/appunni-m/coverage-mcp/blob/main/docs/mcp-reference.md).
