# Pipeline-Stage Tracing: Dump → Compare → Find First Divergence

## Contents

- [Isolate One Input](#step-1-one-input-one-size-two-binaries)
- [Trace Pipeline Stages](#step-2-dump-every-pipeline-stage)
- [Find the First Observed Divergence](#step-3-find-the-first-diverging-point)
- [Trace Internals](#step-4-trace-the-diverged-function-internals)
- [Check the Reference](#step-5-verify-against-reference-source-code)
- [Checklist](#pipeline-trace-checklist)

Use this technique when both implementations expose deterministic, comparable
pipeline boundaries. It narrows the search area without assuming there is only
one defect.

## Step 1: One Input, One Size, Two Binaries

Start with one reproducible input so traces remain attributable. A focused test
may be enough; build standalone binaries only when the existing harness cannot
isolate the input.

Build two standalone binaries:

```rust
// Implementation binary (traces ONE input)
fn main() {
    let data = std::fs::read("/path/to/input").unwrap();
    let result = process(&data, params); // ONE call, all traces from THIS input
}
```

```c
// Reference binary (traces ONE input)
int main() {
    load_input("/path/to/input");
    process(params);  // ONE call, all traces from THIS input
    return 0;
}
```

Run both and diff the traces:

```bash
./trace_impl 2>impl.log
./trace_ref 2>ref.log
diff ref.log impl.log
```

## Step 2: Dump Every Pipeline Stage

Instrument equivalent stable boundaries in both implementations. Start coarse
and add detail only around the earliest observed divergence.

### Example: Font Hinting Pipeline

| Stage | What to Dump |
|-------|-------------|
| Load | Raw input coordinates |
| Segment/Edge Detection | All edge positions (fpos, opos, pos) |
| Edge Hints (Phases 1-4) | Edge positions after each phase |
| Edge Assignment | Which points got touched |
| Strong Adjustment | All grid-fitted coordinates |
| Weak Adjustment (IUP) | Reference pairs used |
| Output | Final coordinates |

### Dump Format

Make traces machine-comparable:

```
[STAGE:reload] ox[0..5]=185,133,64,31,31
[STAGE:edges]  HORZ: fpos=40 pos=40 opos=40 flags=0x04
[STAGE:edges]  HORZ: fpos=120 pos=120 opos=120 flags=0x04
[STAGE:hint_phase1]  edge[0] pos=40→40  edge[1] pos=120→128
[STAGE:align]  pt[14] x=185 TOUCH=Y strong=Y
[STAGE:align]  pt[15] x=133 TOUCH=N weak=Y
[STAGE:iup]  ref=(pt[14]:185, pt[20]:33) → pt[15]=133
[STAGE:final]  pt[15]=200
```

## Step 3: Find the First Diverging Point

Compare stage by stage. The first observed difference bounds where at least one
cause may live; later independent defects may still exist.

### Example: WEAK_INTERPOLATION Bug

```
Stage                    C                           Rust
reload                   ox[0..5]=185,133,64,31,31   same           ✓
compute_edges (HORZ)     5 edges: fpos=40,120,...     same           ✓
hint_edges (phase 4)     pos=0,64,256,348,375         same           ✓
align_edge_points        pt[20] not yet touched       same           ✓
align_strong_points      pt[20] x=33, TOUCHED         pt[20] WEAK     ✗ ← BUG HERE
IUP                      refs (pt[14], pt[20])        refs (pt[14], pt[21])
Final                    pt[15]=201                   pt[15]=200     +1 diff
```

The divergence is at `align_strong_points`. Everything after (IUP refs, final coordinates) is a consequence of pt[20] being classified differently.

## Step 4: Trace the Diverged Function Internals

Once you know WHICH function diverges, trace its internals with finer granularity:

```
align_strong pt[20]:
  C:  flags=0x00 (STRONG), in=(-103,-60), out=(47,36)
  Rust: flags=0x10 (WEAK),  in=(-11,4), out=(32,28)
```

Now trace backward from the different inputs:

```
C:   in_dir from pt[19].out_dir=(-103,-60)
Rust: in_dir from pt[19].out_dir=(-11,4)
  → pt[19] classified differently in build_direction_chain
    → near_limit=9 picked different first-point
      → different u/v chain
```

## Step 5: Verify Against Reference Source Code

Read the EXACT reference function. Look for:

- Sequential checks that our code combined (e.g., XOR first THEN corner check — not both in one `||`)
- Index-delta updates that our code might skip (side effects inside conditionals)
- Early-return paths we missed
- Default values that differ

### Key Finding: Short-Circuit Side Effects

```
// C (afhints.c:1221-1290): XOR check, then corner_is_flat
if (xor_same) {
    // mark as WEAK
} else if (corner_is_flat(in, out)) {
    // SIDE EFFECT: update prev_v->u and next_u->v
    prev_v->u = next_u - prev_v;  // ← THIS CHANGES downstream classification
    next_u->v = -prev_v->u;
}

// Our Rust (BUG):
((in_x ^ out_x) >= 0 && (in_y ^ out_y) >= 0)
    || corner_is_flat(in_x, in_y, out_x, out_y)
// The || short-circuits and skips the delta update!
```

## Pipeline Trace Checklist

When facing unknown divergence, answer these questions in order:

```
[ ] Input data matches reference before processing? → loader correct
[ ] Edge/segment positions match reference? → detection correct
[ ] Positions match after each adjustment phase? → algorithm correct  
[ ] Touch/classification flags match reference? → flag logic correct
[ ] Final coordinates match reference? → interpolation correct
[ ] If all above match but output differs → output path or rasterizer
```
