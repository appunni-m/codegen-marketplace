---
name: performance-parity-optimization
description: This skill should be used when the user asks to profile or optimize an operation, reduce Python/Rust (PyO3) boundary copies, improve CPU/SIMD/GPU performance, increase throughput without behavior changes, or verify an end-to-end speedup claim.
metadata:
  short-description: Optimize measured CPU, GPU, and FFI bottlenecks
---

# Performance and parity optimization

Improve latency, throughput, or resource use for a named workload while keeping
the accepted output and service contract fixed. Base changes on measurements of
the real path. Treat kernel timings, compiler flags, and backend labels as
diagnostics until they explain a gain at the operation boundary that matters.

## Establish the target and the path

Record the requested metric, success limit, representative workload, input
distribution, and measurement boundary. For a public operation, include each
cost its caller pays: normalization, validation, allocation, conversion,
execution, synchronization, materialization, serialization, and output. Keep
microbenchmarks for diagnosis; report them separately from end-to-end results.

Trace the call from its public entry through dispatch and output creation. Note
the source revision, executable/build configuration, hardware, warm or cold
state, relevant caches, and concurrency. Verify that the measured executable
matches the source. When a claim depends on SIMD or device execution, obtain a
per-case dispatch/completion receipt or an equivalent trace and check for
fallbacks. A requested profile or backend name does not prove that it ran.

Choose workloads that cover the expected size and shape distribution, including
small cases where setup dominates, large cases where memory or compute may
dominate, and boundary layouts, sparse/dense inputs, or concurrency levels that
can alter dispatch. Use production-like values and build settings.

## Find and bound the dominant cost

Profile the real operation before rewriting a loop. Attribute elapsed time to
meaningful phases; inspect scaling with bytes/items, fixed call/setup costs,
allocation, copies, queueing, synchronization, and downstream work. For CPU
work, use samples and relevant counters. For memory-heavy work, count full
passes and bytes read, written, copied, or allocated. For asynchronous work,
measure the critical path and completion wait; summed worker or kernel time is
not request latency.

Estimate the attainable gain before investing. Use Amdahl's bound for the
measured fraction being improved and compare useful work with measured compute
or bandwidth ceilings. Treat models as bounds and hypotheses, then check them
against profiles. Read [performance models and measurement evidence](references/performance-research.md)
when making a speedup, bandwidth, or statistical-confidence claim.

Use the evidence to choose a small next change. Common signatures include:

- Flat time across input sizes: inspect dispatch, validation, allocation,
  synchronization, and batching overhead.
- Time proportional to data volume: inspect representation, copies, traversal,
  locality, and achieved bandwidth.
- Superlinear growth: count repeated scans, nested work, or growing queries and
  fix the algorithm or plan before tuning instructions.
- A sharp threshold: correlate it with cache capacity, allocator behavior,
  device limits, spilling, pools, or another observed event.
- High elapsed time with low compute use: measure queueing, locks, I/O, device
  waits, mapping, or backpressure.
- High compute use with low throughput: inspect instructions, branches,
  locality, contention, oversubscription, and saturated bandwidth.

## Optimize from the cause outward

Use this as a search order, not a fixed checklist. Re-profile after a useful
change because the bottleneck can move.

1. Remove redundant or asymptotically expensive work while preserving required
   validation, error order, evaluation, and state changes.
2. Move fewer bytes and cross fewer boundaries. Trace conversions, copies,
   serialization, intermediate buffers, host/device transfers, readback, and
   export. Keep data in a representation that the next stage can consume.
3. Allocate and initialize less. Count allocations and initialized bytes; reuse
   bounded scratch only when its memory, lifetime, synchronization, and stale
   state costs remain acceptable.
4. Improve locality with contiguous access, a useful working set, and tiling
   only when the complete operation improves.
5. Compare serial, SIMD, threading, batching, and accelerator routes on the
   actual workload. Include dispatch, launch, scheduling, occupancy, queueing,
   synchronization, contention, and memory limits.
6. Tune instructions after profiles and generated code identify them as a
   limiting cost. Keep a correct general route for inputs the specialization
   does not prove.

For byte/channel layouts, shared representations, aliases, and exact fast-path
predicates, read [representation and fast-path patterns](references/data-layout-and-fast-paths.md).
For vector loops, threading, and packed tails, read [CPU, SIMD, and parallel
patterns](references/cpu-simd-and-parallel.md). For device execution and data
transport, read [GPU and accelerator patterns](references/gpu-and-accelerators.md).
For database or service paths, read [service and query patterns](references/services-and-databases.md).

## Avoid Python/Rust boundary copies (PyO3)

For each hot payload, map the Python and Rust types, direction, mutability,
owner, lifetime, and allocations across the bridge. Check the exact PyO3 version
and feature set: extraction and construction APIs can have different copy
behavior.

When Rust only reads or sends immutable Python `bytes`, PyO3's `bytes` feature
can extract them as `bytes::Bytes` while retaining the backing allocation. For
example, `value.extract::<Bytes>()?` can pass the shared payload through Rust
channels to an async transport without first copying it into a `Vec`. Keep the
`Bytes` owner alive through the last consumer; converting to `Vec<u8>` copies,
while cloning a `Bytes` handle only adds a reference. Sharing avoids a payload
copy, not extraction, scheduling, or reference-counting overhead.

Mutable `bytearray` and writable buffers need a snapshot unless mutation is
prevented or ownership is transferred exclusively. Do not alias mutable
Python storage across Rust workers just to remove that safety copy. In the
reverse direction, `PyBytes::new(py, rust_slice)` copies. If the consumer
requires Python `bytes`—as ASGI request messages do—retain native Rust storage
through queues and streaming, remove intermediate copies, then make the one
required Python object at the boundary. Avoid unsafe pointer-based `bytes`
construction without a complete lifetime and deallocation proof.

Preserve chunking and backpressure instead of materializing whole bodies.
Bound queued bytes as well as message count when chunk sizes vary. Instrument
crossing calls, copied bytes, Python scheduling, and queue-full wait time; run
small call-heavy and large streaming cases at the complete request/response
boundary.

## Preserve the observable contract

Before admitting a fast path, write down a complete, inexpensive predicate for
every semantic and layout condition it assumes. Preserve validation and send
unproven inputs to the established route.

Compare formulas using the reference types and evaluation order. Check
intermediate widths, overflow, rounding, truncation, saturation, fused
operations, NaNs, signed zero, and boundary values when they apply. Preserve
error order, mutations, metadata, aliases, callbacks, and deferred execution.
A mathematically equivalent expression may not be behaviorally equivalent.

Prove small finite domains exhaustively when practical. Otherwise compare
public results and relevant side effects over extrema, empty and small inputs,
tails, thresholds, adversarial distributions, and every admitted layout. Include
fallback cases and the public path that is intended to dispatch. Read
[representation and fast-path patterns](references/data-layout-and-fast-paths.md)
for conversion, copy-on-write, and native-layout checks.

## Measure the candidate and decide

Run baseline and candidate with the same source snapshot, workload, build,
machine state, cache policy, and operation boundary. Use repeated paired or
interleaved runs where practical; report distributions and uncertainty rather
than relying on a single best sample. Keep construction outside the timed region
only when real callers do the same. Measure required output materialization.

Check representative cases both for regressions and for the requested metric.
For throughput, hold offered load or batch size independent of completion,
increase concurrency gradually, and record successful completions, queueing,
backlog, tail latency, errors/retries, and peak memory at the same operating
point. Do not infer sustained throughput from one-request reciprocal latency.

Accept a change only when contract checks pass, the tested execution path is
known, the gain exceeds measurement noise on the requested metric, and resource,
quality, and tail limits hold. Record the baseline, result, parity evidence,
workload, build, and boundary. If the target still misses, bound further attempts
and use the updated profile to select a different cause.
