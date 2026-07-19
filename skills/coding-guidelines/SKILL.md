---
name: coding-guidelines
description: This skill should be used when the user asks to "review Rust code style", "configure rustfmt", "resolve Clippy lints", "choose Rust names", "define workspace lint policy", "create a Rust review checklist", or needs repository-aware guidance on naming, formatting, API conventions, error policy, concurrency style, and justified lint exceptions.
license: MIT
compatibility: Rust 1.70+
metadata:
  version: "1.0.0"
---

# Rust Coding Standards

This skill adapts selected guidance from Leonardo Maldonado's MIT-licensed
[`rust-skills`](https://github.com/leonardomso/rust-skills) project. Preserve
the bundled [`references/THIRD_PARTY_NOTICES.md`](references/THIRD_PARTY_NOTICES.md)
when redistributing this skill.

Apply standards in this order:

1. Read repository instructions, `rustfmt.toml`, `clippy.toml`, workspace lints,
   and the minimum supported Rust version.
2. Preserve established local conventions unless they conflict with correctness,
   soundness, or an explicit project rule.
3. Use the Rust Style Guide, Rust API Guidelines, rustfmt, and Clippy as the
   default references.
4. Treat third-party style rules as suggestions, not language requirements.

## Naming

- Use `snake_case` for modules, functions, methods, and local bindings.
- Use `UpperCamelCase` for types and traits.
- Use `SCREAMING_SNAKE_CASE` for constants and statics.
- Prefer names that expose domain meaning over implementation detail.
- Follow standard conversion prefixes: `as_` for cheap borrowed views, `to_`
  for conversion that may allocate or copy, and `into_` for ownership-consuming
  conversion.
- Follow collection conventions such as `iter`, `iter_mut`, and `into_iter`.
- Avoid a `get_` prefix for ordinary infallible field accessors. Keep it when
  the surrounding API or operation semantics make the prefix meaningful.

## API Design

- Accept borrowed forms when ownership is unnecessary.
- Return owned values when the result must outlive the input or ownership
  transfer is part of the contract.
- Use newtypes when they prevent unit confusion or invalid domain values.
- Keep public types and trait bounds no broader than required.
- Mark return values `#[must_use]` when silently discarding them is usually a
  defect.
- Document errors, panics, safety requirements, units, ownership, and side
  effects for public APIs.

## Errors And Panics

- Use `Result` for expected operational failures.
- Reserve panic for violated internal invariants or APIs whose contract
  explicitly permits panic.
- Preserve useful error context without erasing structured error types at
  library boundaries.
- Do not mechanically replace every `unwrap` with `expect`; remove avoidable
  panic paths, and explain truly invariant ones.

## Performance And Concurrency

- Require measurement before performance-driven complexity.
- Choose arrays, `Vec`, maps, channels, locks, and atomics from access patterns,
  contention, ordering needs, and MSRV constraints.
- Do not recommend a third-party primitive as a universal replacement for a
  standard-library primitive.
- Keep blocking work off async executors and avoid holding non-async lock guards
  across `.await`.
- State and verify lock ordering and atomic memory-order assumptions.

## Lint Workflow

Run the repository's configured commands first. Typical fallback:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
# Run tests through the repository's approved testing workflow.
```

Do not add blanket `allow` attributes to make the lint run green. Scope an
allow to the smallest item and include a reason when the lint is intentionally
inapplicable.

## Review Output

Report concrete findings with file and line references. Separate:

- correctness or soundness defects
- public API and compatibility risks
- repository-policy violations
- optional style improvements

Avoid presenting personal preference as a mandatory Rust rule.
