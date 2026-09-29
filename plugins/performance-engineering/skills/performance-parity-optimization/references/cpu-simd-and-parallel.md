# CPU, SIMD, and parallel patterns

Load this reference when tuning CPU loops, explicit vector code, work
partitioning, or a serial/SIMD/threaded crossover.

## Inspect the generated work

- Find the dominant function in a profile from the real caller. Hoist invariant
  work and expose contiguous slices/strides only when profiles support the
  change.
- Check whether the compiler already vectorizes a simple loop before adding
  explicit vectors or intrinsics. Inspect optimization remarks and generated
  machine code for packed loads, arithmetic, shuffles, gathers/scatters, stores,
  lane masks, tails, register pressure, and spills.
- Count useful lanes and bytes moved. Interleaved channels can turn a few
  arithmetic operations into many shuffle or extract instructions. Compare a
  safe transpose/shuffle with direct gathers, and measure both over the complete
  operation. Do not assume that a vector-looking source expression maps to one
  instruction.
- Compare scalar, compiler-vectorized, and explicit-vector implementations.
  Keep the least complex one that wins on the admitted workloads.
- Check the project's unsafe-code policy before using target intrinsics. Keep
  architecture-specific routes behind feature detection and preserve a tested
  portable fallback.

## Prove arithmetic and bounds

- Use widened intermediate types only as required by the reference expression;
  preserve rounding points, signedness, saturation, fused operations, and
  reduction order.
- For small finite domains such as byte arithmetic, exhaust the domain and
  compare the proposed expression with the exact reference operation. Keep the
  exhaustive proof in a regression test before removing a clamp, lookup table,
  or intermediate quantization.
- Handle vector tails explicitly. Prove each load and store stays within the
  active input/output span; do not rely on allocation padding unless the
  interface guarantees it. Test short lengths around each vector and word
  boundary.
- Include conversion, allocation, output stores, and materialization in the
  timing. A faster arithmetic kernel can lose after its adapters and copies.

## Partition work only when it pays

- Parallelize independent output ranges and give workers disjoint writes. Keep
  dependencies across pixels, rows, tiles, or requests in the chosen algorithm
  intact.
- Sweep serial and parallel routes over actual shapes and work per task. Choose
  the crossover separately for materially different kernels; total byte count
  alone does not describe scheduling overhead or available parallelism.
- Measure worker count, chunk size, launch/scheduling cost, false sharing,
  nested parallelism, allocation, and memory-bandwidth saturation. Compare
  single-operation latency and aggregate completions under realistic concurrent
  requests.
- Prefer a simple contiguous copy or scalar loop when it reaches the measured
  bandwidth limit. Vectorizing a memory-bound operation can add work without
  reducing elapsed time.

## Useful pattern checks

- For bytewise point transforms, derive the operation on stored samples before
  expanding them into a generic channel representation. If a constant parameter
  maps every input exactly to a shift, mask, or lookup, prove all parameter and
  sample values before specializing it.
- For interleaved input and a different output format, fuse only compatible
  per-element stages and write final output directly. Preserve each required
  intermediate quantization.
- For row-based kernels, compute checked row strides and chunk boundaries once
  outside the inner loop. Keep cross-row filters, cumulative recurrences, and
  error diffusion on a traversal that preserves their dependencies.
- Avoid copying a parallel threshold or vector width from another kernel. A
  pointwise byte transform, a gather-heavy conversion, and a multi-stage filter
  expose different work and memory traffic per task.
