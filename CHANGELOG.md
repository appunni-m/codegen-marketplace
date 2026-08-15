# Changelog

All notable changes to this marketplace are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and plugin versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-08-15

### Added

- Release `rust-development` as 0.3.2 with the `release-rust-crate` skill: an
  evidence-first workflow for SemVer and MSRV review, package inspection,
  workspace ordering, first crates.io publication, GitHub OIDC Trusted
  Publishing, immutable action pins, binary artifacts, clean-consumer checks,
  and fix-forward recovery. Include a deterministic non-publishing release
  audit and realistic evaluation fixtures.

### Fixed

- Pin the testing plugin to Coverage MCP 0.9.0, whose stdio connector
  automatically replaces a verified older daemon on the fixed loopback port.
  New owners use a capability-authenticated graceful handoff; the first
  upgrade from a legacy owner uses its active lease identity. Unknown port
  occupants, different registries, equal-version incompatibilities, and
  downgrade attempts remain fail-closed.
- Keep the installer lock limited to one-time Cargo bootstrap. HTTP clients
  and any number of stdio bridges remain concurrent and never acquire the
  daemon ownership lease.
- Remove the legacy direct-database connector configuration. Stdio and
  compaction clients always route through the shared daemon, which is the only
  process that opens project stores.

## [0.5.0] - 2026-08-15

### Added

- Add a plugin-relative Codex launcher that bootstraps the exact published
  Coverage MCP crate with Cargo under a versioned install lock, caches the
  binary, and then enters the shared-daemon stdio flow automatically.
- Add the testing plugin's `run-coverage-campaign` skill, bounded handoff
  contracts, and evaluation suite for Luna Max execution with Sol High strategy
  and recovery.
- Add the `opensource` plugin with the `opensource-documentation` skill for
  audience-first README flows, source API contracts, community and security
  documentation, release artifacts, and evidence-backed validation.
- Add a deterministic documentation inventory script and cross-project skill
  evaluation cases.

### Changed

- Update Gemini and the non-Codex testing connectors to launch native Rust
  `coverage-mcp connect`; the Codex bootstrap ultimately executes the same
  binary instead of treating the repository as a Python package.
- Align the testing workflow with Coverage MCP schema revision 7 and its
  eleven-tool contract, explicit `get_run_data` run IDs, narrow composable
  coverage projections, and one shared-daemon transport contract.
- Restore automatic shared-daemon startup for the Rust stdio connector: every
  project session reuses one fixed loopback daemon instead of competing for
  repository DuckDB ownership. Only the daemon holds its ownership lease;
  HTTP clients and stdio bridges remain independently concurrent.
- Move the Codex connector declaration into the plugin-root `.mcp.json` used by
  the current bundled-MCP plugin contract.
- Synchronize the marketplace README, testing plugin, agent skill, generated
  host guidance, compatibility declaration, and local cache around the same
  schema-7, eleven-tool shared-daemon contract.
- Pin the automatic Codex bootstrap to Coverage MCP 0.8.6 after its Linux and
  clean-registry release gates pass.
- Pass the pinned Coverage MCP release into the Codex launcher through the
  bundled MCP JSON environment instead of hard-coding it in the launcher.
- Add absolute executable and repository overrides to the Pi MCP installer.
- Add an explicit `--cargo-manifest` Pi launcher and checkout-local Cargo
  instructions so local development uses `cargo run` without a separate build
  or install; non-Codex connectors retain the native executable default.

## [0.4.1] - 2026-07-21

### Changed

- Release the testing plugin as `0.3.1`.
- Update Coverage MCP workflow guidance for `get_run_data`, `cancel_run`, and
  ETA-aware `poll_after_ms` status fetches.

## [0.4.0] - 2026-07-19

### Added

- Expose Coverage MCP to Gemini CLI through the repository's combined Gemini
  extension, using the same `uvx` connector as Codex and Claude Code.
- Preserve Leonardo Maldonado's MIT notice beside the adapted Rust coding
  guidelines and in every generated standalone bundle.
- Include the marketplace MIT license in the independently distributed testing
  plugin.

### Changed

- Release `rust-development` as `0.3.0` and add Gemini-specific test approval,
  idempotency, worktree-measurement, and dashboard guidance.
- Clarify that Pi uses `pi-mcp-adapter` because the marketplace build toolkit
  does not expose Pi as a native target.

## [0.3.0] - 2026-07-18

### Changed

- Adopt Coverage MCP schema revision 7 and its consolidated ten-tool contract.
- Default every agent workflow to compact responses, word-budgeted cursor pages,
  bounded log search, and exact multi-range source queries.
- Require repository, checkout, suite, and worktree lineage validation before
  comparisons, with unknown parent identifiers reported as errors.

## [0.2.0] - 2026-07-18

### Added

- Coverage MCP connector support with one shared user-level daemon and one
  lazily opened DuckDB per shared Git repository.
- Bounded run-log search and exact coverage-line range queries.
- Explicit third-party attribution and preserved MIT license notices.
- Public-release security policy and automated dependency updates.
- Release-readiness checks for upstream-main connector tracking and ignored DuckDB
  state.

### Changed

- Track the Coverage MCP connector from upstream `main` without a release-version
  constraint.
- Replace the duplicated Rust handbook with concise, repository-aware core and
  specialist guidance, and generalize the systematic-debugging workflow.
- Tell users to open the local Coverage MCP dashboard after managed test and
  coverage tasks complete.
- Release the testing plugin as `0.2.0` instead of a local Codex cachebuster.
- Upgrade `@ai-plugin-marketplace/cli` to 0.5 and core to 0.8, enabling the
  toolkit's position-aware lint checks.

### Security

- Restrict the CI workflow token to read-only repository contents.

[0.5.1]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.5.1
[0.5.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.5.0
[0.4.1]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.4.1
[0.4.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.4.0
[0.3.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.3.0
[0.2.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.2.0
