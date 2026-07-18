# Changelog

All notable changes to this marketplace are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and plugin versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.3.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.3.0
[0.2.0]: https://github.com/appunni-m/codegen-marketplace/releases/tag/v0.2.0
