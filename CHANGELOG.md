# Changelog

All notable changes to this marketplace are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and plugin versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Add the testing plugin's `run-coverage-campaign` skill, bounded handoff
  contracts, and evaluation suite for Luna Max execution with Sol High strategy
  and recovery.
- Add the `opensource` plugin with the `opensource-documentation` skill for
  audience-first README flows, source API contracts, community and security
  documentation, release artifacts, and evidence-backed validation.
- Add a deterministic documentation inventory script and cross-project skill
  evaluation cases.

### Changed

- Update the testing plugin and Gemini Coverage MCP connectors to launch the
  native Rust `coverage-mcp connect` executable instead of treating the Rust
  repository as a Python package through `uvx` or `pip`.
- Align the testing workflow with Coverage MCP schema revision 8, explicit
  `get_run_data` run IDs, narrow composable coverage projections, and separate
  stdio versus HTTP-daemon behavior.
- Add absolute executable and repository overrides to the Pi MCP installer.
- Add an explicit `--cargo-manifest` Pi launcher and checkout-local Cargo
  instructions so local development uses `cargo run` without a separate build
  or install; portable plugin manifests retain the native executable default.

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

[0.4.1]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.4.1
[0.4.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.4.0
[0.3.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.3.0
[0.2.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.2.0
