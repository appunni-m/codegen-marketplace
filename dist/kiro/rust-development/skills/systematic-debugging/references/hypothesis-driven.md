# Hypothesis-Driven Debugging: Test Before You Fix

## Contents

- [The Pattern](#the-pattern)
- [Form a Hypothesis](#step-1-form-a-hypothesis)
- [Build a Minimal Test Harness](#step-2-build-a-minimal-test-harness)
- [Run the Hypothesis Test](#step-3-run-the-hypothesis-test)
- [Fix and Verify](#step-4-fix-and-verify)
- [When to Use Hypothesis Testing](#when-to-use-hypothesis-testing)
- [Integrating with Pipeline Tracing](#integrating-with-pipeline-tracing)

For each plausible root cause, design a focused probe that distinguishes it
from competing explanations. Use repository-approved test commands and treat a
probe as evidence for only the inputs and paths it exercises.

## The Pattern

```
Hypothesize → Isolate → Compare → Verify → Fix → Confirm
```

## Step 1: Form a Hypothesis

Based on trace analysis, form a specific hypothesis about where the bug is:

```
❌ VAGUE: "The edge positions are wrong"
✅ SPECIFIC: "sort_and_quantize_widths returns wrong denominator for LiberationSerif 10pt"
✅ SPECIFIC: "render_conic produces different line sequence for curved glyphs at 16pt"
```

## Step 2: Build a Minimal Test Harness

Extract the suspect function and feed it the SAME inputs that C receives:

### Example: Function-level comparison

```rust
// tests/hypothesis_sort_widths.rs
#[test]
fn sort_and_quantize_widths_matches_c() {
    // Input: EXACT same array C receives
    let widths = vec![1200, 1248, 1296, 1344];  // from C trace: LiberationSerif 'H'
    let n = widths.len();
    
    // C output (from fprintf trace):
    //   quantized = [1200, 1280, 1280, 1344], denom=1280
    
    let result = sort_and_quantize_widths(&widths);
    
    assert_eq!(result.quantized, vec![1200, 1280, 1280, 1344], "quantized mismatch");
    assert_eq!(result.denominator, 1280, "denominator mismatch");
}
```

### Example: Bounded fixed-point math comparison

```rust
// tests/hypothesis_fixed_math.rs
#[test]
fn ft_mul_fix_matches_reference_for_boundaries() {
    let cases = [i16::MIN, -1024, -1, 0, 1, 1024, i16::MAX];
    for a in cases {
        for b in cases {
            let c_result = c_ft_mul_fix(a, b);  // run C binary
            let rust_result = ft_mul_fix(a, b);
            assert_eq!(rust_result, c_result, 
                "ft_mul_fix({}, {}) diverges", a, b);
        }
    }
}
```

### Example: Algorithm-level comparison

```rust
// tests/hypothesis_render_conic.rs
#[test]
fn render_conic_matches_c() {
    // Feed identical p0/control/p2, compare line sequence
    let p0 = Point { x: 0, y: 0 };
    let control = Point { x: 64, y: 128 };
    let p2 = Point { x: 128, y: 0 };
    
    let c_lines: Vec<Line> = get_c_render_conic_output(p0, control, p2);
    let rust_lines: Vec<Line> = render_conic(p0, control, p2);
    
    assert_eq!(rust_lines, c_lines, "line sequence differs");
}
```

## Step 3: Run the Hypothesis Test

```bash
# Run only this test — takes seconds, not minutes
cargo test -p my-crate hypothesis_sort_widths -- --nocapture
```

If the probe passes, record that it did not reproduce the defect for those
cases; it may not cover the failing path. If it fails in the predicted way,
the hypothesis gains support—trace the causal path before fixing it.

## Step 4: Fix and Verify

Fix the function, re-run the hypothesis test to confirm, THEN run the full test suite:

```bash
# 1. Fix the function
# 2. Verify hypothesis test now passes
cargo test -p my-crate hypothesis_sort_widths

# 3. Run full suite to confirm no regressions
cargo test -p my-crate --release
```

## When to Use Hypothesis Testing

| Scenario | Hypothesis test | Full suite |
|----------|----------------|------------|
| New suspected bug | ✅ Write a focused probe | Defer only when the focused probe is sufficient for this iteration |
| Verify a fix | ✅ Test the fixed function in isolation | ✅ Run full suite after |
| Regression check | ❌ Not useful | ✅ Run full suite |
| Exploring unknown divergence | ✅ Extract suspect function | ❌ Too slow for iteration |

## Real-World Example: sort_and_quantize_widths

**Symptom:** 47 tests fail for deva, cher, geok scripts. Edge positions differ by 16-32 FU.

**Hypothesis:** The denominator computation in `sort_and_quantize_widths` is wrong.

**Isolation:** Extracted the function, fed it the exact width array from C's trace output.

**Comparison:** Rust returns denom=1216; C returns denom=1280.

**Verification:** Traced function internals. Found integer division truncation: Rust used `widths[n/2] / 2` when C used `(widths[n/2] + 1) / 2` (round-half-up).

**Fix:** Changed to round-half-up. Re-ran hypothesis test: passes. Full suite: -47 failures.

**Time:** Hypothesis test: 2 seconds. Full suite: 45 seconds. 22× speedup for iteration.

## Integrating with Pipeline Tracing

Hypothesis tests work best AFTER pipeline tracing has identified the suspect function:

```
Pipeline trace → Find first divergence → Identify suspect function
                                             ↓
                              Hypothesis test isolates function
                                             ↓
                              Fix confirmed → Full suite
```

Use tracing first when the suspect boundary is unknown. When an error or
invariant already identifies a narrow component, begin with the focused probe.
