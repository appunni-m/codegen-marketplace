import { defineConfig } from '@ai-plugin-marketplace/core';

export default defineConfig({
  version: '0.1.0',
  targets: ['claude', 'codex', 'cursor', 'vercel'],
  description:
    'Evidence-driven performance optimization for CPU, SIMD, parallel, GPU, database, and service workloads.',
  keywords: ['performance', 'profiling', 'benchmarking', 'simd', 'gpu', 'throughput'],
});
