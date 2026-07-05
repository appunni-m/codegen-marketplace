# Root Cause Analysis: Fix the Cause, Not the Symptom

## Contents

- [Anti-Patterns](#anti-patterns-what-not-to-do)
- [Trace Backward](#the-pattern-trace-backward-from-divergence)
- [Read the Reference](#reading-the-reference-source-code)
- [Translated Expressions](#translated-expressions)
- [Document the Fix](#documenting-the-fix)
- [Preserve Evidence](#evidence-to-preserve)

When you've found the first divergence point, resist the urge to "make it match." The goal is to understand WHY it diverges and fix the algorithmic cause.

## Anti-Patterns: What NOT to Do

### Clamping Outputs

```rust
// WRONG: Clamping to match expected
let gy_max = result.bbox.y_max.max(10); // "make it match PIL"

// RIGHT: Find why bbox_y_min differs by 2px
eprintln!("[TRACE] bbox: ox={} oy={} fx={} fy={}", ox, oy, fx, fy);
// Then trace backward to find where the coordinate diverges
```

### Enabling Partial Code Paths

```
// WRONG: Enable WIP code and hope it helps
// "Maybe the phantom-point adjustment will fix it"
// Result: Score DROPS from 1170 to 1140 because edges are wrong

// RIGHT: Fix edge positions FIRST, then enable downstream code
```

### Adding Per-Input Special Cases

```rust
// WRONG: Special case per glyph
if glyph_index == 37 {  // 'B' in NSDB
    adjust_differently();
}

// RIGHT: Find why the algorithm fails for this topology
// The same fix will work for all inputs with that topology
```

## The Pattern: Trace Backward from Divergence

Once you've found the first divergent value, trace backward through the code:

1. **Which function produced the divergent value?** → Trace its internals
2. **Which inputs to that function differ?** → Trace backward to the function producing those inputs
3. **Repeat until you find the original computation that differs**

### Example: WEAK_INTERPOLATION Trace

```
Divergence: pt[20] classified as WEAK instead of STRONG
  ↓
Which function classified pt[20]? build_direction_chain
  ↓
What inputs differ? in_dir and out_dir for pt[20]
  ↓
Where do in_dir/out_dir come from? Previous points' deltas
  ↓
Which previous point differs? pt[19] has different u/v chain
  ↓
Why does pt[19] differ? near_limit=9 picked different first-point
  ↓
Why? C's corner_is_flat() updates delta indices as a SIDE EFFECT
  ↓
Our short-circuit || skipped the delta update
```

## Reading the Reference Source Code

When reading the reference implementation, look for:

### 1. Sequential Checks, Not Combined

```
// WRONG: Combined boolean
if (xor_same || corner_is_flat(in, out)) { ... }

// RIGHT: Sequential checks (C does this)
if (xor_same) {
    // handle case
} else if (corner_is_flat(in, out)) {
    // handle case WITH side effects
}
```

### 2. Side Effects in Conditionals

```c
// C: corner_is_flat has side effects
if (corner_is_flat(in, out)) {
    // This block WON'T execute, but corner_is_flat already modified:
    prev_v->u = next_u - prev_v;  // global state changed!
    next_u->v = -prev_v->u;
}
```

If `corner_is_flat` modifies global state, you can't skip calling it even when the result isn't needed.

### 3. Index Updates After Classification

```c
// C updates indices after classification
if (is_weak) {
    flags |= WEAK_INTERPOLATION;
    prev_v->u = next_u - prev_v;  // THIS changes downstream computation
    next_u->v = -prev_v->u;      // even for points NOT yet visited
}
```

These index updates affect the direction chain for all downstream points. Skipping them causes cascading classification differences.

### 4. Default Values and Edge Cases

```c
// C may have default handling we missed
if (direction == NONE) {
    // C's ft_corner_is_flat() handles this
    // Our code might skip the NONE case entirely
}
```

## Translated Expressions

Do not infer a precedence difference from a surprising result. Check both
languages' rules and make the intended grouping explicit. For example, additive
operators bind more tightly than bitwise AND in both C and Rust, so
`val & !MASK - offset` groups as `val & ((!MASK) - offset)`. If the intended
operation is "mask, then subtract," write `(val & !MASK) - offset` in both
languages and add boundary-focused parity tests.

## Documenting the Fix

Add a comment at the fix site only when the upstream relationship or invariant
would not otherwise be clear:

```rust
// ✅ FIX: Separate XOR check from corner_is_flat to preserve delta side effects
//    C: afhints.c:1276-1290 — sequential if/else if with delta updates
//    Our old: short-circuit || skipped prev_v->u and next_u->v updates
//    Verified: C fprintf trace shows pt[20] classified STRONG after fix,
//              matching C's output. 9 tests fixed, 0 regressions.
```

Keep the regression test as the executable guard; the comment preserves only
the non-obvious upstream relationship.

## Evidence To Preserve

When the repository's commit convention permits a detailed body, record:

```
Fix: <one-line description>

C reference: <file>:<line-range>
What C produces: <exact value>
What Rust produced (old): <exact value>
What Rust produces (now): <exact value>
Root cause: <why it diverged>
Tests fixed: <number>
```

Example:

```
Fix: separate XOR and corner_is_flat checks in build_direction_chain

C reference: afhints.c:1221-1290
C: pt[20] classified STRONG, x=33 after align_strong
Rust (old): pt[20] classified WEAK, skipped in align_strong
Rust (now): pt[20] classified STRONG, matches C
Root cause: short-circuit || skipped delta index updates
Tests fixed: 9 (NSDB BoldItalic: B/g; LiberationSerif: $; etc.)
```
