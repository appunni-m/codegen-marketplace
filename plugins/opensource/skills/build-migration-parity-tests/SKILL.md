---
name: build-migration-parity-tests
description: Build runnable migration parity test suites with input-only fixtures, a live source oracle, public target execution, normalized Results, generic comparison, surface accounting, anti-cheat guards, and managed coverage evidence. Use when porting or reimplementing behavior across languages or runtimes, replacing a legacy implementation, constructing differential or back-to-back tests, migrating fixture corpora, or adding parity coverage for an API, CLI, ABI, protocol, service, file format, or library.
---

# Build Migration Parity Tests

Create or update actual repository files that exercise both implementations.
Do not stop at a report, plan, checklist, or audit. Verification is the final stage
of the build, not the skill's primary deliverable.

Apply one language-agnostic process to API, CLI, ABI, protocol, file format, service, or library
migrations. Own the public-behavior parity harness; this is not a general implementation rewrite
or architecture review.

## Required deliverable

Build one public surface end to end before expanding:

```text
input-only fixture
-> live source oracle
-> live target implementation
-> normalized Result comparison
-> coverage/evidence ledger
```

The source implementation is the oracle for the declared version and contract.
The target implementation is the system under test.
The minimum harness is the manifest, input fixtures, source oracle, target
runner, and comparator.

Create or adapt, using repository-native languages and test tools:

- `tests/fixtures/manifest.yaml`, input JSON, and required input assets;
- a shared Case/Result model and strict fixture loader;
- a live source-oracle adapter with an identity handshake;
- a target runner that calls the public target surface;
- a generic comparator and declared output/error normalization;
- an operation registry/dispatcher checked against manifest rows;
- a parity test entry point plus schema and anti-cheat tests;
- a repository-native test target and managed coverage artifact configuration.

Completion requires runnable checked-in test code for at least one active
surface. Pending surfaces remain classified debt. Do not claim completion from
scaffolding alone.

## 1. Discover before building

1. Read repository instructions, worktree state, test policy, manifests, old
   tests, fixtures, bindings, and public entry points. Preserve user changes.
2. Choose the smallest useful public surface. Record exact source and target
   identities, runtimes, feature flags, plugins, environment, and contract.
3. Inventory source operations and target endpoints. Classify each as `active`,
   `pending`, `unsupported`, `deprecated`, or `non-endpoint`; unclassified names
   are failures. Pending is visible debt, not passing.
4. Locate the native test framework, shared support modules, fixture conventions,
   and maintained command surface. Extend them instead of creating a parallel
   generic framework.
5. Read [the universal standard](references/standard.md) before writing the
   manifest, adapters, comparator, normalization, or coverage contract.

## 2. Build the fixtures and manifest

1. Create exactly one active manifest at `tests/fixtures/manifest.yaml`.
2. Add one surface and its complete operation accounting. Declare output shapes,
   required parameter values, statuses, exclusions, and intended coverage.
3. Write independent input-only cases beneath `tests/fixtures/inputs`. Derive
   success, errors, and values only from live execution.
4. Recursively reject output/error/status expectations, golden data, pixels,
   hashes, oracle paths, and baselines. Use deterministic globally unique IDs:
   `<Surface>.<operation>.<independent_path>`.
5. Resolve assets beneath `tests/fixtures/assets`; reject absolute paths and
   traversal. Replace network dependencies with deterministic local fixtures.
6. Run the static preflight:

```bash
python3 <skill-root>/scripts/audit_parity_fixtures.py <repository> --strict
```

This audit is a build guard, not the parity deliverable.

## 3. Build the executable harness

Implement a repository-native equivalent of:

```text
load_cases(manifest) -> Case[]
run_source(case) -> Result
run_target(case) -> Result
compare(source_result, target_result, policy) -> Diff[]
```

- Make the source adapter verify its runtime/version, isolate ambient state,
  consume only Case inputs, call the public source surface, and emit exactly one
  Result per case. Oracle startup, timeout, crash, non-zero exit, malformed
  output, or result count unequal to input case count is a test failure and
  infrastructure failure, not a target parity result.
- Make the target adapter call the public target API, CLI, ABI, protocol, wire,
  or file-format surface. Target production code must not read fixture/oracle
  paths, launch the source oracle, or branch on test identity.
- Keep wrappers thin: they may convert types, map errors, and manage handles,
  but must not implement algorithms, interpret fixtures, or contain source
  parity hacks.
- Dispatch by declared operation, never case ID. Test that manifest operations,
  input files, and runner arms map both ways with no extras.
- Emit a shared Result envelope containing `case_id`, `status`, and `value` or
  public `error`. Keep transport deterministic and bounded.

## 4. Build the generic comparison

Require matching case ID and status. For `ok`, compare the declared output shape;
for `error`, compare public class/category, stable kind, stable message or
declared pattern, stage, and status code when observable.

- source ok + target ok + equal value = pass;
- source ok + target ok + different value = fail;
- source ok + target error = fail;
- source error + target ok = fail;
- source error + target error + equal public error = pass;
- source error + target error + different public error = fail.

Reject case-id-specific success logic, target output reused as oracle output,
ignored mismatches, and “any error” acceptance. Compare deterministic bytes
exactly. For declared nondeterminism, compare stable public observations and
add deterministic secondary validation.

## 5. Wire and run the harness

1. Add the narrow parity entry point to the existing repository-native test
   command, plus a maintained focused target when the project uses such targets.
2. Add tests that intentionally fail on forbidden fixture keys, duplicate IDs,
   source/target self-comparison, missing results, manifest/runner drift, and
   case-specific comparator branches.
3. Run the preflight, oracle identity check, focused parity target, and relevant
   repository suite. Diagnose every mismatch as data; do not weaken comparison.
4. Run the managed coverage command. Preserve command/run/artifact identity and
   add independent cases for missing intended paths.

Passing parity does not prove coverage. Coverage does not prove parity. Claim
coverage only from a fresh, successfully ingested coverage artifact for the current checkout, active
suite, claimed files, and named dimensions; otherwise report `not proven`.

## 6. Migrate without losing evidence

After the first surface runs, repeat the builder loop surface by surface. Mark
old material deprecated only after its cases are represented. Delete it only
after equivalent or better live parity and coverage evidence exists.

Do not delete first. Migrate, prove, then delete. Never add test-only parity branches
or production branches, coverage exclusions, wrapper algorithms, or case-ID conditionals to
manufacture success.

## Completion report

Report files created/changed, source and target revisions, manifest/input/asset
identities, repository-native commands, run IDs, active pass/fail counts, exact
failing cases, pending operations, retained/removed deprecated evidence, and
worktree status. Include coverage snapshot IDs and percentages only when proven.
