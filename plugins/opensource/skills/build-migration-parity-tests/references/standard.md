# Universal Migration Parity Standard

Use this checklist for any source-to-target behavior migration. Adapt runners
and output shapes to the ecosystem without weakening the evidence rules.

## Contents

- Builder deliverables
- 1. Repository and manifest
- 2. Input cases and assets
- 3. Source and target execution
- 4. Results, comparison, and output shapes
- 5. Public-surface accounting
- 6. Coverage and evidence
- 7. Anti-cheat gates
- 8. Migration, reproducibility, and reporting
- 9. Runtime adapters
- 10. Research basis
- 11. Project profile

## Builder deliverables

This is a test-construction standard. Applying it must create executable,
repository-native files rather than only a design or audit:

```text
manifest + input fixtures + assets
source oracle adapter + target public-surface adapter
shared Case/Result model + operation registry
generic comparator + normalization policy
parity test entry point + anti-cheat/schema tests
maintained test command + managed coverage artifact
```

Use the repository's established test framework and implementation languages.
Do not build a second universal framework beside pytest, unittest, Cargo tests,
Go tests, JUnit, Jest, native C/C++ tests, or the project's equivalent.

The harness boundary should be equivalent to:

```text
load_cases(manifest) -> Case[]
run_source(case) -> Result
run_target(case) -> Result
compare(source_result, target_result, policy) -> Diff[]
```

The source adapter may be a separate pinned process. The target adapter should
exercise the same public surface a real consumer uses. An operation registry may
select handlers by manifest operation; no production or comparator behavior may
select by case ID.

Build one active surface completely before broad scaffolding. Completion means
its checked-in fixtures, adapters, comparison, command, and tests run. A
manifest full of pending rows or unimplemented adapter stubs is not a built
parity suite.

## 1. Repository and manifest

Use one active fixture root:

```text
tests/fixtures/
  manifest.yaml
  assets/
  inputs/
```

Optional roots are `tests/deprecated/`, `tests/support/`, `tests/oracles/`, and
`docs/`. Active runners read only `tests/fixtures`; generated run output belongs
under an ignored build or coverage directory.

The single manifest is `tests/fixtures/manifest.yaml`. It indexes identities,
public surfaces, operations, inputs, assets, parameter/branch/region intent,
out-of-scope behavior, status, and migration state. It is not an output store.

Minimum manifest:

```yaml
version: 1
source:
  name: source-system
  version: "exact-version-or-revision"
  runtime: "verified oracle runtime"
  contract: "observable behavior selected as truth"
target:
  name: target-system
  version: "current checkout-or-build"
  runtime: "public target entrypoint"
  contract: "observable target surface"
policy:
  input_only: true
  live_oracle: true
  result_comparison: true
  coverage_required_for_claims: true
surfaces: []
```

Each surface records stable IDs, source/target paths, input and asset roots,
status, explicit exclusions, and operations. Each operation declares its kind,
public status, input file, output shape, required parameter values, relevant
branches, and coverage regions when applicable.

Operation statuses:

- `active`: has cases and must execute and pass;
- `pending`: known target gap with reason and blocker;
- `unsupported`: source exposes an unsupported/error contract which target must
  match;
- `deprecated`: reference-only material ignored by active runners;
- `non-endpoint`: public name that is not independently callable behavior.

Pending is not passing. Unsupported is tested behavior, not a synonym for
pending. Deprecated evidence cannot satisfy active coverage.

## 2. Input cases and assets

Input document:

```json
{
  "version": 1,
  "surface": "Parser",
  "operation": "parse",
  "cases": [
    {
      "case_id": "Parser.parse.empty_input",
      "operation": "parse",
      "inputs": {
        "assets": {},
        "params": {"text": ""},
        "environment": {}
      }
    }
  ]
}
```

Only `case_id`, `operation`, and `inputs` are allowed on a case. Only `assets`,
`params`, and optional declarative `environment` are allowed under `inputs`.
Environment describes an input condition such as locale, platform feature,
protocol version, runtime option, or plugin availability—not an answer.

Recursively reject these keys from active input JSON:

```text
actual baseline encoded_ref_bytes encoded_ref_path error expect_error
expectation expected golden hash oracle output outputs pixels pixels_hex
raw_path ref_bytes ref_path sha256 status
```

Use globally unique deterministic IDs:

```text
<Surface>.<operation>.<short_independent_path>
```

Reject random values, timestamps, host paths, machine names, and unstable
counters in IDs. Add cases only for a distinct operation, parameter branch,
mode/type, format/protocol variant, asset family, success/error path, boundary,
historical divergence, or documented edge behavior.

Treat two rows as semantic duplicates when surface, operation, parameter class,
branch, mode, asset family, and live source status are the same.

Asset descriptors:

```json
{"kind": "ref", "path": "fonts/example.ttf"}
```

Allowed kinds are `ref`, `inline_bytes`, `generated_input`, `builtin`,
`missing_ref`, and `remote_mock`.

- Canonicalize paths beneath the fixture asset root.
- Reject absolute paths, traversal, and writes to fixture assets.
- Require a deterministic seed and maintained command for generated inputs.
- Replace network dependencies with deterministic local fixtures unless the
  network itself is the public contract.
- Never use generated run output as an active asset without explicit review.

## 3. Source and target execution

The live source oracle must:

- verify exact source and runtime identity;
- isolate user/global state where possible;
- pin dependencies, plugins, features, locale, timezone, and seeds that affect
  observable behavior;
- accept only fixture inputs through a stable transport;
- call the declared source public surface;
- emit one normalized Result for every input case;
- fail on startup, timeout, crash, non-zero exit, malformed output, duplicates,
  missing IDs, extra IDs, or count mismatch;
- record bounded stdout/stderr on infrastructure failure;
- never read target output.

The live target runner must:

- call the target public API, CLI, ABI, protocol, wire, or file-format surface;
- use the same independent input and declared environment;
- convert native values/errors into the shared envelope;
- never read oracle output from target production code;
- never launch the source from target production code;
- never use fixture identity to change production behavior.

Bindings may convert types, map errors, and manage handles/lifetimes. They must
not implement target algorithms, interpret cases, hide mismatches, or move core
behavior out of the target merely to satisfy parity.

## 4. Results, comparison, and output shapes

Success Result envelope:

```json
{"case_id":"Surface.operation.case","status":"ok","value":{}}
```

Error Result envelope:

```json
{
  "case_id": "Surface.operation.case",
  "status": "error",
  "error": {
    "class": "ValueError",
    "kind": "invalid_argument",
    "message": "stable public message",
    "stage": "parse"
  }
}
```

The comparator matches case ID and status first. It then compares the declared
output shape or public error contract. It must be generic and independent of
case IDs.

Common output shapes include scalar, sequence, object, bytes, image, mask,
encoded file, metrics, protocol response, CLI result, and error.

- Structured values compare presence, absence, values, public ordering, and
  observable numeric precision/type.
- Byte-like output compares raw bytes exactly when deterministic. Hashes are
  diagnostic only when raw bytes are practical.
- CLI output can include exit code, stdout, stderr, and generated files.
- Protocol output can include status, headers, body, trailers, and public
  ordering rules.
- Errors compare status, class/category, stable kind, stable message or declared
  pattern, stage, and exit/status code when observable.

Valid reusable normalization includes tuple/list equivalence, deterministic map
ordering, contract-approved path reduction, specified float representation,
runtime JSON encoding for bytes, and platform-neutral newlines when raw bytes
are not the contract.

Invalid normalization includes ignoring bytes or error classes, accepting any
error, arbitrary rounding, hash-only comparison when bytes exist,
case-ID-specific behavior, and suppressing undeclared fields.

For nondeterministic output, declare the unstable fields and reason in the
manifest. Compare stable public observations and add a deterministic secondary
validation such as decoding. Never freeze one nondeterministic run as truth.

Parity truth table:

| Source | Target | Comparison | Outcome |
| --- | --- | --- | --- |
| ok | ok | equal | pass |
| ok | ok | different | fail |
| ok | error | n/a | fail |
| error | ok | n/a | fail |
| error | error | public errors equal | pass |
| error | error | public errors differ | fail |

## 5. Public-surface accounting

For each source namespace and target module:

- discover public names and signatures through the ecosystem's authoritative
  metadata plus explicit project policy;
- classify every public source name and target endpoint;
- require every active operation to name an input file;
- require every discovered active input file to map to one manifest operation;
- require every case operation to map to a runner arm;
- require every runner arm to map back to the manifest;
- report unclassified source/target public names;
- keep lower-level component tests separate from public migration parity.

A public-surface percentage needs an explicit denominator. Do not call a suite
complete merely because all currently listed rows pass.

## 6. Coverage and evidence

Parity pass, public-surface coverage, line coverage, branch coverage, function
coverage, and region coverage are separate measurements.

Use a durable evidence ledger:

1. discover approved commands and latest results;
2. run only the exact approved immutable command, cwd, shell, suite, and
   declared artifacts;
3. retain run identity and poll until terminal;
4. inspect fresh artifact ingestion;
5. capture coverage snapshot IDs;
6. query only the summaries/files/regions needed for the claim;
7. report uncovered dimensions explicitly.

“100% coverage” for a target is valid only when the snapshot is fresh for the
current revision, contains the active parity suite and claimed target, reports
totals for the named dimension, has zero uncovered items in that dimension, and
all active manifest rows passed. Otherwise report `not proven`.

Never equate test success with coverage, coverage with parity, line coverage
with branch/region coverage, or an old/stale artifact with current evidence.

## 7. Anti-cheat gates

Fail the suite or review when:

- active JSON contains embedded expected output/error/status;
- an active runner reads deprecated fixture roots;
- target production code reads oracle or fixture paths;
- target production code launches the source oracle;
- target output becomes oracle output;
- target or wrapper contains test-only parity branches;
- wrappers implement algorithms or source-specific fixture behavior;
- comparator contains case-specific success logic;
- mismatch fields are silently ignored;
- oracle and input result sets differ;
- manifest and discovered input files differ;
- operation, runner-arm, and manifest indexes are not bijective;
- source or target public names remain unclassified;
- coverage exclusions or stale artifacts manufacture completeness.

Audit for direct string/path use, subprocess edges, conditional compilation,
test-only feature flags, broad normalization, exclusions, and case IDs in
production code. Static checks are evidence, not proof of absence.

## 8. Migration, reproducibility, and reporting

Migrate one public surface at a time:

1. inventory old tests and fixtures;
2. identify both public surfaces;
3. create manifest rows;
4. create or retain input-only cases;
5. implement the live source oracle;
6. implement the public target runner;
7. normalize Results;
8. compare exactly;
9. run narrow parity;
10. run the maintained evidence/coverage command;
11. add missing independent behavior paths;
12. mark superseded material deprecated;
13. prove equivalent or better evidence;
14. remove old material;
15. commit.

Do not delete first. Migrate, prove, then delete.

Record for reproduction:

- source and target repository/version/build identities;
- immutable revision and dirty/clean status;
- manifest path and hash;
- input file list and hash;
- asset file list and hash;
- oracle runtime path/version;
- target runtime/toolchain version;
- behavior-relevant dependency/plugin/feature versions;
- command identity and run id;
- coverage snapshot id when claimed;
- counters, terminal status, and exact failing case IDs.

The final report includes commit, changed files, commands, pass/fail counts,
evidence IDs, coverage only when proven, pending rows, deprecated evidence
removed/retained, skipped checks with reasons, and final worktree status.

## 9. Runtime adapters

Adapters change transport, not truth:

- Python/Ruby/JavaScript: isolate environments and lock imports/packages.
- C/C++/Rust/Go: call the public library or CLI, preserve ABI/build modes, and
  separate host tooling from target execution.
- JVM/.NET: pin runtime and dependency resolution; normalize declared public
  exceptions/status, not implementation stack traces.
- CLI: compare exit code, stdout, stderr, and generated files according to the
  declared contract.
- HTTP/gRPC/services: use a deterministic local server topology; compare public
  status, headers/metadata, payload, streaming order, and protocol errors.
- Binary libraries/FFI: keep bindings thin and compare owned bytes, layouts, and
  public error/status behavior without duplicating algorithms in the binding.

## 10. Research basis

- McKeeman, “Differential Testing for Software”:
  <https://dblp.org/rec/journals/dtj/McKeeman98.html>
- LLVM libc differential fuzz tests compare libc implementations:
  <https://libc.llvm.org/dev/fuzzing.html>
- LLVM libFuzzer deterministic-target guidance:
  <https://llvm.org/docs/LibFuzzer.html>
- Reproducible Builds documentation:
  <https://reproducible-builds.org/docs/>
- Bazel test execution and hermeticity specification:
  <https://bazel.build/reference/test-encyclopedia>

These sources support same-input comparison, deterministic inputs/execution,
declared environments, and independently verifiable evidence. The manifest and
anti-cheat rules in this standard are the migration policy, not claims that
those sources define this exact schema.

## 11. pillow-rs project profile

Instantiate the universal roles as:

```text
source implementation = Pillow 12.2.0
source oracle = .oracle-venv/bin/python executing PIL public APIs
target implementation = pillow-rs
target runner = Rust tests calling pillow_rs root public API
coverage ledger = Coverage MCP
active fixture root = pillow-rs/tests/fixtures
single manifest = pillow-rs/tests/fixtures/manifest.yaml
```

Migration order:

1. move Font/ImageFont parity into the single manifest;
2. share input-only validation, oracle execution, Result comparison, and
   manifest-accounting checks;
3. migrate image-backend parity;
4. migrate codec inputs from `image-slash-star` without stored outputs;
5. use `fontdone` for public-surface accounting and pending-route visibility,
   not as the direct schema.

Keep Python and JavaScript bindings thin, keep target behavior in Rust core,
reject output/error expectations in active JSON, require Coverage MCP evidence
for coverage claims, and treat deprecated fixture roots as reference only.
