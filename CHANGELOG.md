# Changelog

Current marketplace changes are recorded here. Detailed behavior and
compatibility claims live in the authored plugin documentation and manifests.

## 0.7.2 - 2026-08-28

### Fixed

- Pin the testing plugin to Coverage MCP `0.15.2`, schema revision 16, and the
  refreshed eight-tool contract.
- Document the ordinary incremental union as the full-shaped `measurement`,
  with run-specific increment/decrement data under `incremental`.

## 0.7.1 - 2026-08-27

### Fixed

- Pin the testing plugin to released Coverage MCP `0.15.1`, including its
  refreshed tools-list digest and exact native bootstrap metadata for the
  incremental-union fix.

## 0.7.0 - 2026-08-26

### Changed

- Upgrade the testing plugin to Coverage MCP `0.15.0`, schema revision 15, and
  the live eight-tool contract.
- Document additive incremental coverage as the deduplicated union of the fixed
  baseline and all selected ordinary artifacts, with a separate diagnostic diff
  that labels selected-subset absence `not_observed` instead of regression.
- Keep composite coverage, exact binary bootstrap, and shared-daemon handoff
  guidance synchronized with the published release.

## 0.6.0 - 2026-08-25

### Changed

- Synchronize the testing plugin with Coverage MCP `0.13.0`, schema revision 14,
  and the eight-tool public contract, including parameterized runs,
  automatic incremental reviews, composite production coverage, and bounded
  duplicate-coverage candidates for named tests.
- Document one-time command registration with optional case-specific arguments,
  explicit baseline snapshot selection, automatic versus standalone incremental
  comparison, and compaction-compatible detail sources.
- Keep the marketplace workflow focused on approval, polling, freshness,
  lineage, budgets, and reporting while the server owns protocol validation and
  evidence semantics.
- Keep the published guidance aligned with the current connector and contract.

## Unreleased
