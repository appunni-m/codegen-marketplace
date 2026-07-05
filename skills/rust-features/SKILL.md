---
name: rust-features
description: This skill should be used when the user asks "what changed in Rust", "which release stabilized this API", "is this feature stable", "what is the latest Rust release", "how do I migrate editions", "does this fit the project MSRV", or needs verified release, edition, standard-library, Cargo, rustdoc, Clippy, beta, or nightly feature information.
license: MIT
compatibility: Rust 1.70+
metadata:
  version: "1.0.0"
---

# Rust Release And Feature Research

Verify release facts at request time. Do not rely on a static "latest version"
table.

## Workflow

1. Read `rust-toolchain.toml`, `rust-toolchain`, `Cargo.toml` edition and
   `rust-version`, plus CI toolchain pins.
2. Run `rustc --version --verbose` and `cargo --version` when local toolchain
   state matters.
3. Use official Rust sources:
   - Rust release posts and release notes for stable changes
   - the Edition Guide for edition migrations
   - the Reference for language semantics
   - standard-library documentation for stabilization versions
   - the Unstable Book and tracking issue for nightly features
4. Separate language changes, standard-library additions, Cargo changes,
   rustdoc changes, and Clippy changes.
5. Confirm whether a feature is stable, edition-gated, nightly-only, deprecated,
   or removed.
6. Compile a minimal example with the requested toolchain when feasibility
   matters.

## Compatibility Analysis

For a proposed feature:

- identify the stabilization release
- compare it with the project's MSRV
- note edition migration requirements
- check target and platform restrictions
- provide a fallback for older supported compilers when practical
- avoid recommending nightly for production without a concrete need and an
  explicit maintenance plan

## Output

Report:

- current project toolchain and MSRV
- requested Rust release or feature
- stability and edition status
- exact impact on the project
- migration or fallback steps
- links to official release notes and reference documentation

Label inference separately from documented behavior.
