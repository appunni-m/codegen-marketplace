# Universal Migration Parity Build Standard

Use this procedure for API, CLI, ABI, protocol, service, and file-format
migrations. The exact data interfaces live in
[the manifest contract](manifest-contract.md) and
[the evidence contract](evidence-contract.md).

## Contents

- 1. Build order
- 2. Public inventory
- 3. Specification and input design
- 4. Oracle and target execution
- 5. Comparison
- 6. Coverage
- 7. Benchmarks
- 8. Aggregation and documentation
- 9. Anti-cheat and migration gates
- 10. Domain profiles

## 1. Build order

Create executable repository-native files:

```text
canonical manifest + parity/coverage/benchmark inputs + assets
public inventory discovery + strict loaders + reference validation
live oracle adapters + public target-profile adapters
workflow result model + generic comparator
managed coverage integration + deterministic benchmark runner
fixed lane results + compatibility-aware aggregate
generated specification/status documentation + drift checks
```

Use the existing project test framework and maintained command surface. Avoid a
second generic framework beside Cargo tests, pytest, Go tests, JUnit, Jest,
native C/C++ tests, or the project equivalent.

Build one end-to-end slice to validate the interface, then continue to the
requested denominator. A broad manifest with placeholders is not a scoped
suite.

## 2. Public inventory

1. Pin the source contract and public-inventory authority.
2. Discover source names from authoritative metadata plus explicit project
   policy.
3. Discover public target names for every consumer-visible target boundary.
4. Preserve source spelling, case, nesting, and symbol identity.
5. Classify independently observable behavior as endpoints. Include constants,
   records, layouts, error domains, macros, and protocol operations when they
   have public observations.
6. Classify only namespaces, imports, markers, or metadata without an
   independent observation as non-endpoints.
7. Model each public target once and each behavior-relevant
   backend/runtime/feature combination as a target profile.
8. Fail when a source name or target endpoint is absent, duplicated, or mapped
   only by an undeclared convenience alias.

Do not use fixture directory names as public identities. For example, a
filesystem folder named `font` can store `PIL.ImageFont` cases only when
`storage_slug` explicitly records that mapping.

## 3. Specification and input design

### Manifest

Declare:

- exact oracle and component versions;
- public targets without mutable checkout revisions;
- target profiles;
- structured commands;
- one indexed input file set per lane;
- reusable many-to-many coverage components;
- canonical public surfaces and operations;
- typed source parameters and observable result contracts;
- per-target bindings and support declarations;
- semantic requirements and performance budgets;
- explicit lane applicability;
- generated documentation destinations.

The manifest is product and test policy. It is not the current run ledger.
Runner readiness, pass/fail, measurements, snapshots, and current revisions
belong in results.

### Parity inputs

Represent public behavior as workflows:

```text
assets + ordered public steps + bindings + observed steps
```

This supports:

- a single function call;
- constructor plus method;
- handle creation, ABI call, and cleanup;
- detect, inspect, verify, decode, and encode pipelines;
- CLI setup and invocation;
- protocol request sequences.

Validate every step operation, receiver, parameter name, parameter type,
binding, asset, target profile, observation, and requirement reference.

Do not put expected behavior in inputs. An invalid call is represented only by
its invalid public arguments; the live oracle determines the public error.

### Coverage inputs

Select canonical parity cases and/or declared maintained commands. Map the plan
to target profiles, reusable components, and coverage requirements.

Use coverage-only commands for defensive/internal paths only when necessary.
They cannot satisfy parity requirements and must not move production behavior
behind coverage-only code.

### Benchmark inputs

Declare:

- measured subjects: oracle and/or target profiles;
- input kind: parity case, workflow, process command, or artifact;
- timing boundary and measured step IDs;
- metrics;
- warmup, iterations, samples, concurrency, and cache policy;
- correctness gate;
- optional weighted suites.

Keep actual measurements and baseline comparisons in results.

### Assets

Keep all active assets deterministic and provenance-bound. Input digests are
valid because they identify stimulus bytes. Generated assets need a maintained
command and seed. Reject absolute paths, traversal, undeclared network access,
and generated oracle/target output reused as an active input.

## 4. Oracle and target execution

The oracle adapter must:

- verify exact implementation/runtime/component identity;
- isolate ambient state where possible;
- pin locale, timezone, plugins, features, and seeds that affect behavior;
- accept only the declared workflow and assets;
- call the public source contract;
- emit exactly one workflow result per selected case;
- never read target output.

The target adapter must:

- verify target/profile identity and record immutable revision later in the
  result;
- exercise the same public surface a consumer uses;
- accept the independent workflow and assets;
- convert native public values and errors into the shared result interface;
- never launch the oracle from production code;
- never read source results or fixture expectations;
- never change behavior by case ID.

Bindings may convert types, map public errors, and manage handles or lifetimes.
They must not implement target algorithms, interpret semantic fixture intent,
or hide target gaps.

Treat adapter startup, timeout, crash, malformed transport, duplicate IDs,
missing IDs, extra IDs, and count mismatch as infrastructure failures.

## 5. Comparison

Compare:

1. selected case and target-profile ID sets;
2. workflow completion status;
3. observed step ID sets;
4. public ok/error status per step;
5. declared observation fields and values.

Use exact equality for deterministic scalar, structured, byte, image, mask,
layout, and encoded-file observations unless the public contract declares
another fixed comparison.

Valid reusable normalization includes:

- tuple/list representation equivalence when the contract does not distinguish
  them;
- deterministic map ordering;
- platform-neutral newlines when raw bytes are not the contract;
- bounded removal of runtime object addresses;
- a declared numeric representation rule.

Invalid normalization includes:

- accepting any error;
- ignoring bytes, error class, or status;
- arbitrary rounding;
- hash-only comparison when bytes are available;
- case-specific branches;
- suppressing undeclared target fields;
- using expected values from input fixtures.

For public nondeterminism, compare declared stable observations and add a
deterministic secondary validation. Do not freeze one prior output as truth.

## 6. Coverage

Parity case mapping, public-surface coverage, and function/line/branch/region
coverage are distinct.

Run only maintained approved coverage commands. Preserve:

- command and run identity;
- target profile and immutable revision;
- selected cases/commands;
- input digests;
- collector version;
- artifact-ingestion and snapshot identity;
- component/file identity;
- integer covered and total counts;
- uncovered locations;
- threshold calculations.

Claim a dimension only when its snapshot is fresh for the current compatible
target profile and selected suite. Test success is not coverage. Line coverage
is not branch or region coverage. Old snapshots are not current evidence.

Do not add exclusions, unreachable shims, or coverage-only production behavior
to manufacture a threshold.

## 7. Benchmarks

Run a workload only after its declared correctness gate:

- `parity_pass` — compatible parity evidence passes;
- `source_target_match` — a benchmark workflow preflight matches;
- `successful_execution` — appropriate for a target-only operational
  measurement;
- `not_applicable` — only for non-behavioral artifact measurement.

Preserve:

- manifest and input identity;
- workload and suite policy;
- timing boundary;
- measured subject and profile;
- machine, OS, architecture, CPU, memory, power mode, and toolchain;
- raw-sample reference and descriptive statistics;
- absolute or relative budget calculation;
- baseline compatibility decision.

Support more than call latency. Real migrations may need throughput,
allocations, peak/resident memory, artifact size, encoded size, startup time,
CPU time, process-level comparisons, and weighted workload suites.

Never compare results across incompatible workload, machine, target profile,
backend, feature, revision, or measurement policy.

## 8. Aggregation and documentation

Aggregate by manifest digest, input digests, requirement, operation, target
profile, immutable revision, and lane-specific context.

Missing, stale, failed, cancelled, invalid, dirty-target, and incompatible
evidence stays visible as `not_proven`. A dirty target is never current proof.
Do not infer pass from a support declaration or an old result.

Generate:

1. public specification reference from manifest and indexed inputs;
2. current parity, coverage, and benchmark status from the aggregate.

Record generator/schema version, manifest identity, target profile/revision,
and evidence IDs in generated output. Regenerate and diff checked-in pages or
publish immutable output.

## 9. Anti-cheat and migration gates

Fail review or CI when:

- a consumer maintains a parallel operation inventory;
- an unknown field or unsupported schema is accepted;
- a parameter/input/reference is not declared;
- expected or observed output appears in active parity inputs;
- measured coverage or performance appears in manifest/input files;
- source and target ID sets differ;
- production or wrapper code reads fixture/oracle paths;
- target code launches the oracle;
- comparator behavior selects by case ID;
- wrappers implement migrated algorithms;
- mismatches are ignored;
- coverage exclusions manufacture completeness;
- budget pass ignores correctness;
- incompatible evidence is aggregated;
- generated docs hide missing/stale evidence;
- deprecated fixtures are removed before mapping and equivalent evidence.

When migrating old material:

1. inventory old operations, scenarios, assets, results, and consumers;
2. map operations and scenarios to canonical requirements;
3. migrate independent inputs and deterministic assets;
4. replace embedded expectations with live oracle execution;
5. add coverage and benchmark specifications where applicable;
6. run equivalent or stronger evidence;
7. move old files to a deprecated archive;
8. prove active consumers no longer read the archive;
9. remove only with retained mapping and evidence.

Fixture deprecation is not public API deprecation.

## 10. Domain profiles

### High-level object API

Use nested public surfaces for modules, classes, and methods. Represent receiver
construction as a workflow setup step. Preserve binding targets separately when
Rust, Python, JavaScript, native, WASM, CPU, or GPU consumers expose distinct
public behavior.

### C ABI and compile-time surface

Inventory functions, constants, enum variants, flags, macros, records, tags,
types, and errors. Treat compile visibility, value, size, alignment, offsets,
error codes, and handle lifecycle as observable endpoints where applicable.
Use workflows for allocation/call/release sequences. Keep C/WASM wrappers thin.

### Image and file-format surface

Use one public format surface per format and explicit operations such as
detect, inspect, verify, decode, decode-sequence, encode, and encode-sequence.
Map one asset to several observed operations without copying outputs into
inputs. Keep generated oracle observations in results, not in an executable
coverage matrix treated as input truth.

### CLI and protocol surface

Model argv/stdin/files or request/response fields as declared public
parameters. Compare exit/status, stdout/stderr, headers, body, trailers,
streaming order, generated files, and public errors according to the operation
result contract.
