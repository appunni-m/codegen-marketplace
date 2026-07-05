---
name: crate-info
description: This skill should be used when the user asks to "look up a crate", "check a crate version", "find crate features", "explain why a dependency is present", "compare Cargo.toml with Cargo.lock", "plan a crate upgrade", or needs current registry metadata, version-specific documentation, MSRV constraints, enabled features, and dependency paths.
license: MIT
compatibility: Rust 1.70+
metadata:
  version: "1.0.0"
---

# Crate Information

Distinguish four different answers:

- **declared**: the requirement in `Cargo.toml`
- **resolved**: the exact version in `Cargo.lock`
- **available**: versions published by the registry
- **compatible**: versions allowed by the requirement, MSRV, features, and
  surrounding dependency graph

Never call the newest published version the project's version without checking
the manifest and lockfile.

## Workflow

1. Inspect the relevant `Cargo.toml`, workspace dependency table, and
   `Cargo.lock`.
2. Use `cargo metadata --format-version 1` for package identities, features,
   targets, and resolved dependency edges.
3. Use `cargo tree -i <crate>` to explain why a crate is present.
4. Use current primary sources for changing facts:
   - crates.io API or crate page for published versions and metadata
   - docs.rs for version-specific API documentation
   - the crate repository for release notes and migration guidance
5. Check the selected version's declared `rust-version` before recommending an
   upgrade.
6. State whether a feature is default, optional, target-specific, or enabled
   transitively.

Use `cargo info <crate>` when the installed Cargo supports it. Fall back to the
registry API rather than guessing.

## Upgrade Analysis

Before recommending a version change:

- identify direct and transitive dependants
- compare enabled features
- check semver-breaking release notes
- check MSRV and edition requirements
- note duplicate major versions already in the graph
- run the repository's tests and lint commands after editing

Treat a semver-compatible update as lower risk, not zero risk.

## Output

Return a compact report containing:

- crate name and purpose
- declared requirement
- resolved version
- latest relevant published version
- enabled features and their origin
- MSRV or toolchain constraints
- dependency path
- documentation, registry, repository, and release-note links
- recommended next action, with uncertainty called out
