---
name: unsafe-review
description: This skill should be used when the user asks to "review unsafe code", "audit unsafe Rust", "check FFI soundness", "review raw pointer usage", "verify Send or Sync implementations", "write a SAFETY comment", or needs an evidence-based review of unsafe blocks, unsafe functions, layout assumptions, aliasing, initialization, provenance, panic safety, or foreign ownership.
license: MIT
compatibility: Rust 1.70+
metadata:
  version: "1.0.0"
---

# Unsafe Rust Review

Review unsafe code from its contract outward. The presence of `unsafe` is not a
finding by itself, and a `SAFETY` comment is not proof.

## Workflow

1. Inventory every `unsafe` block, `unsafe fn`, `unsafe trait`, `unsafe impl`,
   union access, FFI declaration, raw-pointer conversion, and manual layout
   assumption in scope.
2. Identify the safe API or caller contract exposed around each unsafe
   operation.
3. Write down every required invariant before judging the implementation.
4. Trace where each invariant is established and whether safe callers can break
   it.
5. Review cleanup, panic, cancellation, and partial-initialization paths.
6. Run focused verification tools where applicable.
7. Report findings first, ordered by severity, with exact file and line
   references.

## Invariant Checklist

Check only categories relevant to the operation:

- **Validity**: non-null, aligned, dereferenceable, initialized, and valid for
  the access size and duration
- **Aliasing**: shared and exclusive references obey Rust's aliasing model
- **Provenance**: pointer arithmetic and integer round-trips preserve the
  provenance required by the operation
- **Bounds**: offsets, lengths, capacities, and `isize::MAX` constraints hold
- **Layout**: size, alignment, field offsets, discriminants, and ABI match the
  external contract
- **Ownership**: allocator, deallocator, transfer, borrowing, and drop
  responsibility are unambiguous
- **Initialization**: `MaybeUninit`, `set_len`, unions, and out-pointers never
  expose invalid values
- **Lifetimes**: references and callbacks cannot outlive backing storage or
  library handles
- **Concurrency**: manual `Send` or `Sync`, atomics, callbacks, and foreign
  thread entry satisfy synchronization requirements
- **Panic safety**: unwinding or abort behavior cannot expose invalid state or
  cross a boundary that forbids unwinding

## FFI

Verify against the actual foreign header and ownership documentation. Check:

- ABI and calling convention
- C-compatible field and parameter types
- nullability and sentinel values
- string encoding and termination
- callback lifetime and thread rules
- allocator pairing
- error transport
- unwind behavior

Do not assume every FFI struct needs the same representation strategy; derive it
from what crosses the boundary.

## Documentation

Require public unsafe functions and traits to document caller obligations under
`# Safety`. Require each unsafe block or impl to explain why its obligations are
met at that location.

Reject comments that merely restate the operation:

```rust
// SAFETY: `index < len` was checked above, and `base` points to the allocation
// backing `slice` for at least `len` initialized elements.
unsafe { base.add(index).read() }
```

## Verification

Use tools as evidence, not proof:

```bash
cargo miri test
cargo clippy --workspace --all-targets --all-features -- -D warnings
```

Run tests through the repository's approved testing workflow.

Add sanitizer, fuzz, loom, or platform-specific tests when the code involves
FFI, concurrency, parsing hostile lengths, or complex initialization.

Consult current official Rust Reference, Nomicon, standard-library, and Miri
documentation for disputed semantics. Mark uncertain aliasing or provenance
claims as open questions instead of asserting unsoundness without support.

## Review Output

For each finding include:

- severity
- file and line
- violated invariant
- path from safe input to unsafe operation
- concrete failure mode
- smallest sound fix
- missing test or documentation

If no defect is found, state that clearly and list residual assumptions that
could not be verified.
