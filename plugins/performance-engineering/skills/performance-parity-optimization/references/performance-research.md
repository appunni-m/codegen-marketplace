# Performance models and measurement evidence

Use these sources to ground claims about speedup limits, vectorization,
accelerator costs, and measurement uncertainty. They justify the checks in the
skill; none predicts the winner for an unmeasured workload. Pages were checked
on 2026-09-29. Prefer the current documentation for the compiler, runtime, and
hardware actually under test.

## Models and compiler behavior

- **Fixed-work speedup bound:** [Amdahl, “Validity of the Single Processor
  Approach to Achieving Large Scale Computing Capabilities” (1967)](https://doi.org/10.1145/1465482.1465560).
  If fraction `f` of baseline elapsed time is accelerated by factor `s`, then
  the ideal fixed-work whole-program speedup is at most
  `1 / ((1 - f) + f / s)`. This bound assumes the remaining work is unchanged;
  it does not model changing queues, contention, data volume, or load.
- **Compute and memory ceilings:** [Williams, Waterman, and Patterson,
  “Roofline: An Insightful Visual Performance Model for Multicore
  Architectures” (2009)](https://doi.org/10.1145/1498765.1498785). The roofline
  model relates arithmetic intensity to compute and bandwidth ceilings. Use
  measured traffic and sustained rates; theoretical peaks are ceilings, not
  expected application results.
- **Vectorization decisions:** [LLVM Auto-Vectorization documentation](https://llvm.org/docs/Vectorizers.html).
  LLVM has loop and SLP vectorizers, checks legality, and uses target-aware cost
  models; successful vectorization still does not guarantee a faster operation.
  The documentation also describes vectorization remarks and notes that
  floating-point reductions can change order unless stricter operations or
  relaxed-math assumptions allow a different transformation.

## Device execution and transport

- **NVIDIA CUDA:** [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)
  recommends profiling realistic workloads, including host/device transfers in
  measurements, and minimizing transfers or keeping intermediate data on the
  device when the workflow permits. Its timer guidance warns that asynchronous
  API calls can return before work completes.
- **AMD HIP/ROCm:** [HIP performance guidelines](https://rocm.docs.amd.com/projects/HIP/en/latest/how-to/performance_guidelines.html)
  describe profiling kernel execution, bandwidth, occupancy, API calls, and
  timeline relationships among host operations, launches, transfers, and
  synchronization. They make corresponding transfer and batching
  recommendations for HIP workloads.
- **NVIDIA timeline attribution:** [Nsight Systems post-collection analysis](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html)
  separates CUDA API time, queue time, and kernel time. Select the relevant
  vendor/runtime profiler on other platforms; do not treat a device timer as
  end-to-end latency.

## Benchmark uncertainty and load shape

- **Repeated samples and uncertainty:** [Criterion.rs analysis guide](https://bheisler.github.io/criterion.rs/book/analysis.html)
  describes sample-based analysis, outlier reporting, bootstrap confidence
  intervals, and median absolute deviation. Criterion is one implementation;
  use equivalent statistics from the chosen benchmark system and interpret
  intervals against the workload and observed noise.
- **Open and closed workload models:** [Grafana k6 open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
  documents that closed-model iteration starts depend on the previous
  iteration completing, so slower response can lower offered arrival rate.
  Use an open/arrival-rate model when the question is behavior under a fixed
  incoming rate; use closed workloads when they represent the real caller.
