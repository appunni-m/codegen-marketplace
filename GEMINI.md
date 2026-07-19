# Rust Development

Rust engineering plugin for implementation, review, debugging, documentation,
crate research, coding standards, and unsafe-code analysis.

## Overview

Use the narrowest matching skill. Prefer repository policy and current toolchain
evidence over generic advice.

## Usage

Skills activate from the request. Use `rust-development` for general
implementation or review, and select a specialist directly when it is the
narrower match.

## Skills

- **rust-development** - Idiomatic implementation, ownership, errors, testing, performance, and API design
- **systematic-debugging** - Hypothesis-driven debugging and first-divergence tracing
- **rust-documentation** - Rustdoc, doctests, and public contract documentation
- **coding-guidelines** - Repository-aware style, naming, lint, and review policy
- **crate-info** - Selected and available crate versions, features, and dependency context
- **rust-features** - Stable release, edition, and feature research
- **unsafe-review** - Unsafe Rust, FFI, layout, aliasing, and soundness review

## Coverage MCP

This Gemini extension also exposes Coverage MCP for approved test execution,
coverage history, exact missing lines, and worktree baseline comparisons.

- Require human approval of the exact command, working directory, and artifact
  paths before registering or running a test command.
- Start with `project_context(detailed=false)` before rerunning an approved
  suite.
- Use one stable `idempotency_key` for retries of the same intended run.
- Treat a missing worktree snapshot as not measured, not unchanged.
- Open <http://localhost:59471/> only after a test or coverage task completes;
  do not open the browser automatically.
