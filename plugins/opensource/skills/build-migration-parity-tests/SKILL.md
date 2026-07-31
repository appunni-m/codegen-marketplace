---
name: build-migration-parity-tests
description: Build runnable migration specifications and evidence systems with a fixed public-surface manifest, input-only parity workflows, managed coverage plans, deterministic benchmark workloads, live source and target execution, strict result interfaces, aggregation, documentation, and anti-cheat gates. Use when porting or reimplementing behavior across languages or runtimes, replacing a legacy implementation, constructing differential or back-to-back tests, migrating fixture corpora, or adding parity, coverage, and benchmark accountability for an API, CLI, ABI, protocol, service, file format, or library.
---

# Build Migration Parity Tests

Create or update executable repository files. Do not stop at an audit, design,
or name inventory.

Build one fully specified public slice first. Continue through the complete
authority-defined denominator when the request is project-wide.

```text
manifest specification
  + parity workflows  -> live oracle + public targets + comparator -> parity result
  + coverage plans    -> managed instrumented execution            -> coverage result
  + benchmark inputs  -> correctness-gated measurements            -> benchmark result
compatible lane results -> aggregate status -> generated documentation
```

## Load the contracts

Read these normative references before changing a manifest, input, result,
aggregator, or generated page:

1. [Manifest and input contract](references/manifest-contract.md)
2. [Evidence contract](references/evidence-contract.md)
3. [Universal build standard](references/standard.md)

Use fixed versioned interfaces and reject unknown fields. Treat
operation-declared parameter names as data inside the fixed contract, not a
dynamic schema. Improve the interface only with a reviewed schema version,
coordinated consumer changes, deterministic migration, and validation tests.

## Required deliverables

Create or adapt repository-native equivalents of:

```text
tests/fixtures/manifest.yaml
tests/fixtures/assets/
tests/fixtures/inputs/{parity,coverage,benchmark}/

load_manifest -> ManifestSpec
load_parity_inputs -> ParityCase[]
run_oracle(case) -> WorkflowResult
run_target(case, target_profile) -> WorkflowResult
compare(source, target, operation_policy) -> Comparison

load_coverage_inputs -> CoveragePlan[]
run_managed_coverage(plan) -> CoverageResult

load_benchmark_inputs -> BenchmarkWorkload[]
verify_correctness(workload) -> GateResult
run_benchmark(workload) -> BenchmarkResult

aggregate(compatible_results) -> StatusReport
render_specification(manifest, inputs) -> Document[]
render_status(status_report) -> Document[]
```

Also add:

- public inventory discovery and manifest/inventory bijection checks;
- oracle, target, profile, command, operation, component, case, plan, workload,
  suite, and requirement reference checks;
- strict unknown-field and unsupported-schema tests;
- public source and target identity handshakes;
- generic result comparison and declared normalization;
- repository-native parity, coverage, benchmark, aggregation, docs, and drift
  commands;
- anti-cheat tests for circular oracles, target fixture access, case-specific
  comparison, hidden mismatches, stale evidence, and coverage exclusions.

## 1. Discover the actual contracts

1. Read repository instructions, worktree state, existing manifests, tests,
   fixtures, bindings, benchmark tools, coverage tooling, and public entry
   points. Preserve user changes.
2. Identify the authoritative public denominator and exact source version.
3. Inventory every independently observable public endpoint and every
   non-endpoint public name. Preserve public spelling and case. Use explicit
   storage slugs only for filesystem paths.
4. Identify every oracle, public target, and behavior-relevant target profile.
   Model wrappers and backends separately when consumers can observe them.
5. Locate the repository-native command surface and extend it. Do not create a
   parallel universal test framework.
6. Inventory deprecated fixture roots. Map operations, requirements, inputs,
   assets, and evidence before moving or deleting anything.

## 2. Write the specification

1. Create one active manifest and no parallel operation inventory.
2. Declare pinned oracles, target contracts, target profiles, structured
   commands, input indexes, reusable coverage components, canonical surfaces,
   and generated documentation destinations.
3. For each operation, declare the public source signature, typed parameter
   table, observable result contract, target bindings, per-target support,
   exhaustive requirements, and explicit parity/coverage/benchmark
   applicability.
4. Keep current revisions, runner readiness, blockers caused by current
   execution, pass/fail, measured counts, timings, snapshots, and run IDs out
   of the manifest.
5. Never mark `support.status: deprecated` merely because old fixtures moved.
   Public API lifecycle and fixture migration state are different facts.

## 3. Write input-only execution specifications

1. Create parity workflows from fixed steps, typed arguments, deterministic
   assets, bindings, observations, target profiles, and requirement IDs.
2. Use the same workflow independently for the live oracle and each public
   target. Do not embed expected status, values, errors, pixels, encoded bytes,
   or output hashes.
3. Create coverage plans that select canonical parity cases and/or declared
   commands, target profiles, and reusable coverage components. Do not place
   counts, percentages, snapshots, or outcomes in coverage inputs.
4. Create benchmark workloads with explicit subjects, input kind, timing
   boundary, measured steps, metrics, warmups, iterations, samples,
   concurrency, cache state, correctness gate, and optional weighted suites.
   Do not place measurements, baselines, or regression outcomes in benchmark
   inputs.
5. Allow input asset digests; they identify stimulus bytes. Reject expected
   output digests.
6. Validate all declared parameter names/types, paths, references,
   requirement mappings, and index bijections.

Run the static reference audit:

```bash
python3 <skill-root>/scripts/audit_parity_fixtures.py <repository> --strict
```

Use `--manifest <relative-path>` when the repository has an approved
non-default active manifest path. Block-style YAML requires PyYAML; JSON-form
YAML works with the Python standard library.

The audit proves specification shape and mapping only. It does not prove live
parity, coverage, performance, result compatibility, or documentation
freshness.

## 4. Build the executable lanes

- Verify oracle identity before execution. Fail startup, timeout, crash,
  malformed transport, missing IDs, extra IDs, or result-count mismatch as
  infrastructure errors.
- Call each target through the public consumer surface. Keep bindings limited
  to type conversion, public error mapping, and handle/lifetime management.
- Dispatch by manifest operation, never case, plan, or workload ID.
- Compare the declared observation set and public status before values. Compare
  deterministic bytes exactly. Apply only declared reusable normalization.
- Run managed coverage from the selected plan and retain run, artifact,
  snapshot, command, input, target, backend, and feature identity plus integer
  covered/total counts.
- Run benchmarks only after their correctness gate. Retain workload,
  measurement policy, subject, machine, toolchain, samples, statistics, and
  budget evaluation.
- Emit distinct fixed parity, coverage, and benchmark result artifacts. Never
  collapse them into one lossy result type.

## 5. Aggregate and document

Join artifacts only when manifest/input/asset digests, target profile, immutable
revision, runtime, backend, features, and lane-specific identity are
compatible. Render missing, stale, cancelled, invalid, failed, dirty-target, or
incompatible evidence as `not_proven`.

Generate:

- a specification reference from manifest plus indexed inputs;
- current status from the compatible aggregate.

Record manifest digest and evidence IDs in every generated page. Regenerate and
diff checked-in documentation, or publish it from immutable artifacts.

## 6. Migrate deprecated material safely

1. Map every old operation and scenario to the canonical manifest and
   requirement IDs.
2. Map or replace every old input and asset.
3. Run equivalent or stronger live parity, coverage, and benchmark evidence.
4. Move the old tree to a clearly deprecated archive with its mapping record.
5. Delete only after no active runner or consumer reads it and compatible
   evidence is retained.

Do not delete first. Do not weaken tests, thresholds, comparison, or fixture
scope to manufacture migration completion.

## Completion report

Report:

- commit and worktree status;
- changed files and maintained commands;
- source, target, profile, manifest, input, asset, and evidence identities;
- public inventory represented / authoritative inventory;
- complete operation contracts / endpoints;
- mapped parity, coverage, and benchmark requirements;
- parity pass/fail/not-run counts and exact failures;
- covered/total counts for each claimed coverage dimension and snapshot ID;
- benchmark budget pass/fail/not-proven counts and environment identity;
- generated-document freshness;
- deprecated evidence retained, moved, or removed;
- skipped checks and remaining risks.

Use a numerator and denominator for every percentage. Attach a fresh run or
snapshot identity to every execution claim.
