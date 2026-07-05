---
name: rust-development
description: Write, refactor, and review Rust code using repository-aware ownership, borrowing, error handling, testing, performance, trait, lifetime, and API-design guidance. Use for general Rust implementation tasks; prefer a narrower specialist skill for documentation, unsafe code, crate research, release features, coding policy, or systematic debugging.
license: MIT
compatibility: Rust 1.70+, Cargo
metadata:
  version: "1.2.0"
  upstream: "https://github.com/apollographql/skills/tree/main/skills/rust-best-practices"
allowed-tools: Bash(cargo:*) Bash(rustc:*) Bash(rustfmt:*) Bash(clippy:*) Read Write Edit
---

# Rust Development

Apply these guidelines when writing, reviewing, or refactoring Rust code.
This skill adapts Apollo GraphQL's MIT-licensed Rust best-practices material;
the distributed notice is in `references/THIRD_PARTY_NOTICES.md`.

## Specialist Routing

Use the narrowest specialist skill alongside this core guidance when needed:

- `coding-guidelines` for repository style, naming, formatting, and lint policy
- `rust-documentation` for rustdoc, doctests, and public API contracts
- `unsafe-review` for unsafe Rust, FFI, layout, provenance, and soundness
- `crate-info` for dependency versions, features, MSRV, and upgrade research
- `rust-features` for releases, editions, stabilization, beta, and nightly
- `systematic-debugging` for root-cause analysis and implementation parity

## Quick Reference

### Borrowing and Ownership

- Borrow when the callee only needs temporary access; take ownership when the
  callee must retain, transform, or transfer the value.
- Prefer `&str` and `&[T]` over `&String` and `&Vec<T>` for read-only inputs.
- Small, cheap-to-copy `Copy` types are usually good pass-by-value candidates;
  use profiling and API ergonomics rather than a fixed byte threshold.
- Use `Cow<'_, T>` when an API benefits from returning or accepting either a
  borrowed value or an owned replacement.

### Error Handling

- Return `Result<T, E>` for fallible operations; avoid `panic!` in production.
- Avoid `unwrap()` and `expect()` on recoverable production paths. They can be
  appropriate for documented invariants that cannot fail in a valid program.
- Prefer typed errors at library boundaries. Report-style errors such as `anyhow`
  are often useful at application boundaries, but are not limited to binaries.
- Prefer the `?` operator over `match` chains for error propagation.
- Implement `From` for automatic error conversion via `?`.

### Lifetimes

- Rely on lifetime elision when relationships remain clear; annotate lifetimes to
  express API relationships or when required by the compiler.
- Three elision rules: (1) each reference parameter gets its own lifetime,
  (2) a single input lifetime is assigned to all output lifetimes,
  (3) `&self`/`&mut self` methods assign the self lifetime to all outputs.
- Annotate when the relationship between lifetimes is non-obvious:
  ```rust
  fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
      if x.len() > y.len() { x } else { y }
  }
  ```
- In structs that hold references, annotate the lifetime on the struct.

### Pattern Matching

- Prefer `match` for exhaustive handling of enums.
- Use `if let` for single-pattern extraction:
  ```rust
  if let Some(value) = optional { /* use value */ }
  ```
- Use `while let` for iterator-like patterns:
  ```rust
  while let Some(item) = iter.next() { /* process item */ }
  ```
- Use `let else` for early return on pattern failure:
  ```rust
  let Some(value) = config.get("key") else { return Err(...) };
  ```
- Destructure structs and enums inline when only a few fields are needed.

### Closures

- Use `|args| body` syntax. The compiler infers the `Fn`/`FnMut`/`FnOnce` trait.
- Closures capture variables by the least restrictive borrow by default.
- Use `move` when a closure must own its captures. Scoped APIs can sometimes let
  threads or async work borrow instead.
- `FnOnce` — may consume captures and is callable at least once.
- `FnMut` — may mutate captures and can be called repeatedly.
- `Fn` — accesses captures without mutation and can be called repeatedly; this
  does not by itself make the closure thread-safe.

### Generics and Dispatch

- Choose generics for compile-time polymorphism and `dyn Trait` for runtime type
  erasure; benchmark when dispatch cost matters.
- Use `dyn Trait` when runtime polymorphism or type erasure is worth its allocation,
  indirection, and object-safety constraints—for example heterogeneous collections
  or stable plugin/API boundaries.
- Place ownership and allocation where the data model requires them; avoid
  boxing solely to hide an unresolved design choice.
- `impl Trait` in return position for simple cases; named generics when the caller
  needs to constrain the type.

### Standard Library Traits

Consider these traits for public types when their semantics fit:

| Trait | When to implement |
|-------|-------------------|
| `Debug` | Developer diagnostics; redact or customize sensitive fields |
| `Display` | Types meant for user-facing output |
| `PartialEq`, `Eq` | Types that can be compared for equality |
| `PartialOrd`, `Ord` | Types with a natural ordering |
| `Hash` | Types used in `HashMap`/`HashSet` keys |
| `Clone` | Types where explicit duplication makes sense |
| `Copy` | Small types trivial to copy (no heap data, no `Drop`) |
| `Default` | Types with a sensible default value |
| `From<T>` / `Into<T>` | Type conversions that cannot fail |
| `TryFrom<T>` / `TryInto<T>` | Type conversions that can fail |

### Idiomatic API Design

Follow naming conventions for method prefixes:

| Prefix | Usage |
|--------|-------|
| `new` | Constructors: `Vec::new()`, `String::new()` |
| `is_` | Boolean predicates: `is_empty()`, `is_some()` |
| `with_` | Builder-style construction or copy-and-modify: `with_capacity()` |
| `try_` | Fallible operations: `try_reserve()` |
| `from_` | Conversion from another type: `from_raw_parts()` |
| `into_` | Owned conversion: `into_bytes()` |
| `to_` | Conversion that borrows `self` and may allocate or copy: `to_lowercase()` |
| `as_` | Cheap borrowed view or conversion: `as_str()` |

### Newtype Pattern

Wrap primitive or foreign types to prevent semantic confusion and enforce invariants:

```rust
// Before — easily confused
fn process(user_id: u64, order_id: u64) { /* which is which? */ }

// After — type-safe
struct UserId(u64);
struct OrderId(u64);
fn process(user_id: UserId, order_id: OrderId) { /* unambiguous */ }
```

Use the newtype pattern to:
- Prevent unit confusion (meters vs feet, dollars vs cents)
- Enforce validation at construction ("parse, don't validate")
- Implement foreign traits on foreign types (via wrapper)

### Extension Traits

Add methods to types defined in other crates:

```rust
trait StringExt {
    fn is_palindrome(&self) -> bool;
}

impl StringExt for String {
    fn is_palindrome(&self) -> bool {
        self.chars().eq(self.chars().rev())
    }
}
```

Keep extension traits narrow and focused. Watch for method resolution
conflicts — the inherent method always wins.

### Interior Mutability

Use when the borrow checker forbids mutation that is actually safe:

- `Cell<T>` — Whole-value interior mutation without handing out references;
  `get()` additionally requires `T: Copy`.
- `RefCell<T>` — Runtime-checked shared or mutable borrows (panics on violation).
- `Mutex<T>` / `RwLock<T>` — Thread-safe interior mutability.

Choose `Cell` for whole-value operations and `RefCell` when scoped borrows are
required. Both are single-threaded; use synchronization primitives for shared
cross-thread mutation.

### RAII and Drop Guards

Leverage `Drop` for deterministic cleanup:

```rust
// Scope guard — restore state on drop
struct Guard<F: FnOnce()>(Option<F>);
impl<F: FnOnce()> Drop for Guard<F> {
    fn drop(&mut self) {
        if let Some(f) = self.0.take() { f(); }
    }
}

// Usage: release an acquired resource when leaving the scope.
let resource = acquire_resource()?;
let _guard = Guard(Some(|| release_resource(resource)));
// The resource is released even if the function returns early.
```

Use `std::mem::forget` only when absolutely necessary — prefer `Drop` for cleanup.

### Modules and Visibility

- `pub` makes an item visible to the parent module (and all ancestors).
- `pub(crate)` — visible within the crate.
- `pub(super)` — visible to the parent module.
- `pub(in path)` — visible within the given path.
- Private items (no `pub`) are visible only within the current module and its children.
- Let `rustfmt` and the repository's import conventions determine grouping.
- Use `pub use` for re-exports to create a clean public API surface.

### Performance

- Benchmark an optimized profile representative of deployment; debug performance
  is not a reliable proxy for production.
- Run `cargo clippy -- -D clippy::perf` for performance hints.
- Avoid cloning in loops. Choose `.iter()`, `.iter_mut()`, or `.into_iter()` based
  on whether the loop should borrow, mutably borrow, or consume the collection.
- Prefer iterators over manual loops; avoid intermediate `.collect()` calls.
- Be mindful of monomorphization bloat — many generic instantiations increase
  binary size. Extract non-generic inner functions when possible.

### Linting

Run regularly:

```bash
cargo clippy --all-targets --all-features --locked -- -D warnings
```

Key lints to watch:
- `redundant_clone` — unnecessary cloning
- `large_enum_variant` — oversized variants (consider boxing)
- `needless_collect` — premature collection

Configure workspace lints deliberately rather than copying a universal deny
list. For example:

```toml
[lints.clippy]
all = "warn"
correctness = "deny"
```

When the MSRV is Rust 1.81 or newer, prefer `#[expect(clippy::lint)]` over
`#[allow(...)]` with a justification comment. Use a narrowly scoped `allow` for
older MSRVs.
Run `cargo clippy --all-targets --all-features` in CI with `-D warnings`.

### Testing

- Name tests descriptively: `process_should_return_error_when_input_empty`.
- Keep each test focused on one behavior; use as many assertions as that behavior
  needs to make failures clear.
- Use doc tests for public API examples:
  ```rust
  /// Adds two numbers.
  ///
  /// ```
  /// use my_crate::add;
  /// assert_eq!(add(2, 3), 5);
  /// ```
  pub fn add(a: i32, b: i32) -> i32 { a + b }
  ```
- Consider the `insta` crate (and optional `cargo-insta` CLI) for reviewable
  snapshots of generated or structured output.
- Use `#[cfg(test)]` modules; dev dependencies go in `[dev-dependencies]`.

### Type State Pattern

Encode valid states in the type system to catch invalid operations at compile time:

```rust
use std::marker::PhantomData;

struct Connection<State> {
    /* fields */
    _state: PhantomData<State>,
}

struct Disconnected;
struct Connected;

impl Connection<Disconnected> {
    fn connect(self) -> Connection<Connected> {
        /* transition logic */
        Connection { _state: PhantomData }
    }
}

impl Connection<Connected> {
    fn send(&self, data: &[u8]) {
        /* only connected connections can send */
    }
}
```

Beyond simple typestate, combine with generics to encode complex state machines
(e.g., a serializer that tracks whether a root, struct, or property is being written).

### Documentation

- `//` comments explain *why* — safety invariants, workarounds, design rationale.
- `///` doc comments explain *what* and *how* for public APIs.
- Make durable `TODO`s actionable with an issue or owner when repository policy
  requires it: `// TODO(#42): migrate to new parser`.
- Consider `#![warn(missing_docs)]` or `#![deny(missing_docs)]` for public
  libraries after deciding how generated and internal-public APIs are handled.
- Doc comments should avoid restating the name and signature — focus on context,
  preconditions, and examples the reader couldn't guess.

### Iterators

- Use iterator combinators for transformations and loops when control flow is
  clearer; neither form is inherently more idiomatic in every case.
- Chain adapters rather than collecting intermediate results:
  ```rust
  let result: Vec<_> = items
      .iter()
      .filter(|x| x.is_valid())
      .map(|x| x.transform())
      .collect();
  ```
- Implement `IntoIterator` for types that represent collections.
- Prefer the form that makes ownership, short-circuiting, and intent clearest.

## Gotchas

- `cargo build` defaults to debug mode — benchmark and profile with an optimized
  profile representative of deployment.
- The `?` operator converts error types via `From` — implement `From` for
  automatic error conversion between error types.
- `#[cfg(test)]` modules are compiled alongside non-test code; put test-only
  dependencies in `[dev-dependencies]` in `Cargo.toml`.
- `RefCell<T>` is not `Sync` — use `Mutex<T>` or `RwLock<T>` for cross-thread
  shared state.
- The orphan rule prevents implementing a foreign trait for a foreign type —
  use the newtype pattern as a workaround.
- `mem::forget` is safe and will not run `Drop` — be careful with types that
  rely on `Drop` for correctness (mutex guards, scope guards).
- `String` is not `Copy`; `&str` is preferred for function parameters.
- Async Rust may introduce `Pin` and task-specific `Send + 'static` bounds.
  Futures can be dropped while suspended, so design cancellation-safe state
  transitions around `.await` points.
