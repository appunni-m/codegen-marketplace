# Porting Protocol: 12-Step C → Rust Debugging

## Contents

- [Reference provenance and versions](#step-1-establish-a-single-source-of-truth-for-references)
- [Boundary comparison and tracing](#step-3-compare-at-the-boundary-not-the-output)
- [Root-cause and failure categories](#step-5-fix-root-cause-not-symptoms)
- [Workspace and evidence safety](#step-7-preserve-working-state-before-experimenting)
- [Parity and reference traces](#step-9-define-the-required-parity)
- [Systematic loop](#step-12-systematic-debugging-loop)

This protocol was developed during a FreeType autohinter port. Adapt each step
to the repository, reference contract, and risk of the change.

## Step 1: Establish a Single Source of Truth for References

Every test fixture (JSON, binary, SHA) MUST be generated from the EXACT external reference implementation, version-matched. Document:

- **What** generated it (PIL? raw C library? our own code?)
- **Which version** (PIL 12.2.0 bundles FreeType 2.14.3 — use THAT version)
- **How to regenerate** (one script, reproducible from a clean checkout)

If references are regenerated from the code under test, tests are meaningless. Self-referential fixtures pass 100% and prove nothing.

## Step 2: Version-Lock ALL Reference Generators

Before writing a single line of comparison code, verify every reference source uses the same upstream version:

```
Reference matrix generator → FreeType 2.14.3?
PIL (if used for refs)     → bundles FreeType 2.14.3?
System C library           → FreeType 2.14.3?  (often 2.13.x)
Vendored C source          → FreeType 2.14.3?
Your Rust port baseline    → FreeType 2.14.x?
```

Even a patch-version mismatch can change reference output. Check version and
build configuration before interpreting parity failures.

## Step 3: Compare at the Boundary, Not the Output

When pixels differ, do NOT iterate on `getmask()`/`getbbox()` hoping to stumble on the bug. Instead:

1. Pick ONE failing glyph (start simple: `A`, `|`, `-`).
2. Dump its raw input data from BOTH C and Rust **before** any processing. They must match.
3. Dump intermediate state after each major processing stage.
4. Find the FIRST stage that diverges.
5. Everything downstream of that stage is a consequence, not a cause.

**Binary search the divergence.** If point N is the first mismatch, the bug is in whatever function touched point N.

## Step 4: Build the C Reference WITH Instrumentation

Do not try to access internals via Python ctypes — the struct offsets are fragile. Instead:

```bash
# Build reference from vendored source with debug tracing
cd reference-lib && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug -DREF_DEBUG_LEVEL_TRACE=ON
make -j$(nproc)
```

Then use environment variables to enable per-module trace output. Compare the reference's internal function traces with our equivalent.

## Step 5: Fix Root Cause, Not Symptoms

Common anti-patterns to avoid:

- **Clamping outputs to match expected values.** If `getbbox` returns (0,7,4,8) and the reference expects (0,7,4,10), the fix is NOT `gy_max.max(10)`. The fix is finding why `bbox_y_min` differs by 2px.

- **Enabling code paths that amplify bugs.** Phantom-point advance adjustment needs correct edge positions first. Enabling it with wrong edges makes things worse.

- **Adding special cases per glyph.** Each special case is a future bug. Find the algorithmic root cause and fix it once.

- **Renaming files/directories mid-debug.** Churn obscures real diffs. Settle names early.

## Step 6: Categorize Failures Before Fixing

Before touching code, classify every failure:

```
SHA-only (bbox correct):     subpixel coverage difference
Bbox wrong:                  edge position difference
Size wrong:                  advance or metrics difference
Empty/zero output:           pipeline broken entirely
```

Each category has a different root cause. Mixing them wastes time.

## Step 7: Preserve Working State Before Experimenting

Inspect existing changes and preserve them without overwriting user work. Use
a separate worktree, a patch, or another recoverable technique appropriate to
the repository. Do not create commits or discard files without authorization.

## Step 8: Document the Divergence, Not Just the Fix

When you find a bug, document:
- What reference produces (exact value)
- What our implementation produces (exact value)
- Which reference function/line the code diverges from
- Why it diverges (off-by-one? wrong sign? missing case?)

This lets the next person verify the fix without re-deriving the diagnosis.

## Step 9: Define The Required Parity

Define parity from the external contract. Some ports require byte-identical
output; others permit numeric tolerances, platform differences, or documented
intentional deviations. A source diff alone does not prove behavioral parity.

## Step 10: Compare Reference Trace Output

When stuck, add bounded tracing to the implementation and compare equivalent
fields with the reference's trace output. Increase verbosity only around the
suspect stage and remember that instrumentation can itself affect timing or
behavior.

## Step 11: Preserve Verification Evidence

Keep durable evidence in regression tests, review notes, issues, or commit
messages. Add a source comment only when future maintainers need a local
invariant, upstream reference, or explanation for an intentional divergence.

## Step 12: Systematic Debugging Loop

Use this loop to narrow parity bugs systematically:

**Step A — Compare per-pass intermediate state.** Add deterministic temporary
traces for stable fields at each coarse processing pass.

**Step B — Binary search on data index.** Once you know index N is the first mismatch, grep the reference source for the function that touches index N.

**Step C — Compare relevant data structures.** Around the suspect phase, add
only the fields needed to distinguish the remaining hypotheses.

**Step D — Check relevant reference helpers.** Treat skipped or simplified
behavior as a hypothesis to verify, not automatically as a defect.

**Step E — Audit translated expressions.** Add explicit parentheses when the
intended grouping is not obvious, and verify semantics against both languages'
references. Do not assume a precedence difference without checking it.
