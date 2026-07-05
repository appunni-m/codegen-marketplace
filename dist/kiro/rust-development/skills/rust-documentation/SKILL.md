---
name: rust-documentation
description: This skill should be used when the user asks to "fix missing docs", "write Rust docs", "improve rustdoc", "document a Rust API", "make Rust documentation world class", "review Rust documentation", "cargo doc warnings", "missing_docs", "broken intra doc links", "doctests", or wants professional Rust API documentation that clarifies inputs, outputs, errors, panics, invariants, examples, and why an API exists.
license: MIT
compatibility: Rust 1.70+, Cargo, rustdoc
metadata:
  version: "1.0.0"
allowed-tools: Bash(cargo:*) Bash(rustdoc:*) Bash(rg:*) Read Write Edit
---

# Rust Documentation

Write Rust documentation that helps humans and AI agents use and maintain the
API correctly. Passing `missing_docs` is the floor; useful contracts are the
goal.

## Core Rule

Do not add filler documentation. Every public doc should clarify at least one
of these:

- what problem the item solves
- accepted inputs, units, ownership, modes, and byte layout
- returned values, output shape, and side effects
- errors, panics, safety requirements, and invariants
- why the item is public or when to choose it over related APIs
- exact compatibility or parity behavior when the crate mirrors another system

Never use `#[allow(missing_docs)]` to finish a documentation task unless the
user explicitly approves that policy.

## Workflow

1. **Generate docs first**
   - Run `RUSTDOCFLAGS="-D warnings" cargo doc -p <crate> --no-deps` when a
     package is known; otherwise use the narrowest workspace command available.
   - Run `cargo test -p <crate> --doc` when examples or crate docs are edited.
   - Inspect generated docs or source around reported items before writing.

2. **Classify the API**
   - **Surface API**: downstream users or bindings call this directly.
   - **Internal-public API**: public for tests, generated code, backends, or
     bindings; not an ergonomic user interface.
   - **Parity-sensitive API**: mirrors std, C, Python, Pillow, database, wire
     protocol, or other external behavior exactly.
   - **Generated/mechanical API**: macro, registry, enum variants, bindings, or
     repeated descriptors.

3. **Document by contract**
   - Start modules with the domain, entry points, boundaries, and shared
     conventions.
   - Start types with their role, invariants, and why the type exists.
   - Start functions with behavior and destination semantics, not the function
     name rewritten as a sentence.
   - Add `# Errors` for public `Result` functions.
   - Add `# Panics` for public panic paths.
   - Add `# Safety` for public unsafe functions and unsafe traits.
   - Add examples only when they are accurate, compile, and teach a real usage.

4. **Make generated docs useful**
   - For variants and fields, use concise docs only after module/type docs carry
     the broader contract.
   - For operation registries or macros, document the alignment rules: variant,
     key, implementation, generated metadata, shader/FFI/wire layout if any.
   - Prefer metadata-backed generated docs over hand-copying dozens of weak
     repeated comments.

5. **Review like a user**
   - Look for docs that hide required input shape, byte order, coordinate
     inclusivity, ownership, lifetime, feature flag, or error behavior.
   - Replace "does X" boilerplate with the reason, contract, or edge case.
   - Remove stale comments that conflict with code.

## Rustdoc Shape

Use conventional sections when they add real information:

```rust
/// Converts raw RGB bytes into the destination mode.
///
/// # Inputs
///
/// - `pixels`: tightly packed RGB triplets, one row after another.
/// - `width` and `height`: output dimensions in pixels.
///
/// # Returns
///
/// One byte per destination pixel in row-major order.
///
/// # Errors
///
/// Returns [`Error::InvalidLength`] when `pixels.len() != width * height * 3`.
/// Returns [`Error::UnsupportedMode`] when `mode` is not implemented.
```

Prefer intra-doc links such as [`crate::Image`] or [`std::io::Read`] over plain
text names. Run strict rustdoc after adding links.

## API Class Patterns

### Surface API

Surface docs must answer:

- what should the caller pass
- what comes back
- when the call allocates, mutates, defers, blocks, or performs I/O
- what failures mean
- which examples represent normal usage

### Internal-Public API

Say why the item is public and who should use it:

```rust
/// Operation descriptor shared by the high-level API and compute backends.
///
/// # Internal Contract
///
/// This is public for integration tests and backend registration. Downstream
/// callers should prefer [`Image::resize`]. New variants must stay aligned with
/// the registry key and backend implementation.
```

### Parity-Sensitive API

Name the upstream behavior and the relevant units:

```rust
/// Converts RGB to luma using Pillow's rounded BT.601 fixed-point formula.
///
/// This uses Pillow's integer coefficients, not the `image` crate's sRGB
/// luminance weights. The output has the same dimensions as input and one byte
/// per pixel.
```

### Generated or Mechanical API

Short docs are acceptable only when the surrounding module/type explains the
contract:

```rust
/// Right edge of the crop box, exclusive, in source image pixels.
right: u32,
```

Avoid this:

```rust
/// Right.
right: u32,
```

## Anti-Patterns

Do not add:

- docs that only restate an identifier
- vague claims like "Pillow-like", "safe", or "fast" without a contract
- examples that do not compile unless marked `no_run` or `ignore` with a reason
- promises not enforced by code or tests
- giant duplicated paragraphs across many functions
- `TODO` docs with no issue, owner, or concrete follow-up
- `#[allow(missing_docs)]` as a shortcut

## Verification

Use the narrowest package name when possible:

```bash
RUSTDOCFLAGS="-D warnings" cargo doc -p <crate> --no-deps
cargo test -p <crate> --doc
cargo fmt --all -- --check
rg -n 'allow\s*\(\s*missing_docs\s*\)|allow\s*\[\s*missing_docs\s*\]' <crate>/src <crate>/Cargo.toml
```

When documentation touches examples, feature flags, generated code, public
contracts, or parity-sensitive behavior, also run the crate's relevant normal
tests. Report any existing warnings separately instead of hiding them.
