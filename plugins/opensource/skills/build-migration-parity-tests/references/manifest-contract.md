# Manifest and Input Contract

This file is normative for `migration-parity/manifest@2` and its three input
interfaces. Unknown fields are errors. The manifest is a specification, inputs
are executable stimuli, and results are generated evidence.

Read [the evidence contract](evidence-contract.md) for result and aggregate
interfaces. Read [the universal standard](standard.md) for the build workflow.

## Contents

- 1. Truth boundaries
- 2. Canonical layout and identity
- 3. Manifest interface
- 4. Public surfaces and operations
- 5. Requirements and lane policy
- 6. Parity input interface
- 7. Coverage input interface
- 8. Benchmark input interface
- 9. Asset and value interfaces
- 10. Completeness and evolution

## 1. Truth boundaries

Keep four stores separate:

| Store | Contains | Must not contain |
| --- | --- | --- |
| Manifest | Public inventory, oracle and target contracts, support declarations, required behavior, lane applicability, coverage policy, performance budgets, command interfaces | Pass/fail, measured counts, timings, run IDs, current revisions, snapshots |
| Parity input | Public calls and workflows, input assets, requirement mapping, target-profile selection | Expected values, expected errors, stored oracle output |
| Coverage input | Test/case selection, target profile, coverage components, command selection, requirement mapping | Covered counts, percentages, exclusions created to pass, snapshot IDs |
| Benchmark input | Workloads, measurement boundaries, subjects, repetition policy, workload weights, requirement mapping | Timings, baselines, regressions, budget outcomes |

Generated parity, coverage, benchmark, aggregate, and documentation artifacts
live outside the active input tree.

`support.status` is a declared target product contract. It is not measured
proof. Runner readiness and pass/fail are results. Do not store `active`,
`pending`, `blocked`, `passing`, or `failing` in the manifest.

Deprecating an old fixture tree is not deprecating a public API. Keep old-suite
migration mapping under `tests/deprecated/` or another repository-native
archive. Use public lifecycle metadata only when the source API itself is
deprecated.

## 2. Canonical layout and identity

Prefer:

```text
tests/fixtures/
  manifest.yaml
  assets/
  inputs/
    parity/
    coverage/
    benchmark/
```

The manifest indexes every active input file. Consumers discover operations
from the manifest and input index, never from a parallel hard-coded inventory.
Generated outputs belong under ignored result, coverage, benchmark, or build
directories.

Use public spelling and case:

- `PIL.ImageFont`, not `font`;
- `PIL.ImageFont.FreeTypeFont`, not a flattened convenience alias;
- `FT_Render_Glyph`, not a lower-cased dispatcher name;
- `PNG`, not a filesystem slug, when `PNG` is the public format identity.

Surface IDs may contain dots. Operation IDs contain the exact public member or
symbol name. `storage_slug` is the explicit filesystem-safe mapping and is
never a second public identity.

Case, plan, workload, and suite IDs share one global executable-item namespace.
Requirement, command, component, oracle, target, and target-profile IDs are
globally unique within their own kind. IDs are stable data, not timestamps or
random UUIDs.

## 3. Manifest interface

The exact top-level keys are:

```yaml
schema: migration-parity/manifest@2
scope: {}
oracles: []
targets: []
target_profiles: []
commands: []
interfaces: {}
input_index: {}
coverage_components: []
surfaces: []
documentation: {}
```

Do not add a numeric `version`; the schema identifier is authoritative.

### `scope`

Exact keys:

```yaml
scope:
  id: project-public-contract
  mode: full
  inventory:
    authority: path-or-tool-defining-the-denominator
    revision: exact-source-version-or-revision
    command_id: inventory
```

`mode` is:

- `slice` — the declared denominator is an explicitly selected vertical slice;
- `full` — the declared denominator is the entire authority-defined public
  contract.

This is scope policy, not a completion result. Every operation included in
either mode must be fully specified. A name-only placeholder is invalid.

### `oracles`

Each oracle has exact keys:

```yaml
- id: pillow
  name: Pillow
  version: 12.2.0
  runtime: CPython 3.12
  identity_command_id: oracle-identity
  contract: Public observable PIL behavior
  components:
    - id: freetype
      name: FreeType
      version: 2.14.3
```

Oracle version is pinned. `components` records behavior-relevant bundled codec,
runtime, or library versions. It is an array of exact
`id`/`name`/`version` objects.

Several oracles are allowed because one project may use a runtime
implementation, a public ABI header, and a format specification for different
operations. Every operation selects exactly one oracle.

### `targets` and `target_profiles`

Target declarations contain no current checkout hash:

```yaml
targets:
  - id: pillow-rs-core
    name: pillow-rs
    runtime: Rust public crate API
    identity_command_id: target-identity
    contract: Public Rust image and font behavior

target_profiles:
  - id: rust-cpu
    target_id: pillow-rs-core
    backend: cpu
    features: [default]
```

Exact target keys are `id`, `name`, `runtime`, `identity_command_id`, and
`contract`. Exact target-profile keys are `id`, `target_id`, `backend`, and
`features`.

A target is a public implementation boundary. A target profile is one
behavior-relevant runtime/backend/feature configuration. Generated results
record the immutable target revision and exact runtime; the manifest does not.

### `commands`

Commands are structured interfaces:

```yaml
commands:
  - id: parity
    argv: [make, migration-parity-test]
    cwd: .
    timeout_seconds: 900
```

Exact keys are `id`, `argv`, `cwd`, and `timeout_seconds`. `argv` is a non-empty
array, not a shell string. `cwd` is repository-relative. Do not put secrets or
observed output in commands.

### `interfaces`

```yaml
interfaces:
  parity:
    input_schema: migration-parity/parity-input@1
    result_schema: migration-parity/parity-result@1
    command_id: parity
  coverage:
    input_schema: migration-parity/coverage-input@1
    result_schema: migration-parity/coverage-result@1
    command_id: coverage
  benchmark:
    input_schema: migration-parity/benchmark-input@1
    result_schema: migration-parity/benchmark-result@1
    command_id: benchmark
  aggregation:
    input_schemas:
      - migration-parity/parity-result@1
      - migration-parity/coverage-result@1
      - migration-parity/benchmark-result@1
    result_schema: migration-parity/status-report@1
    command_id: aggregate
```

Lane interface keys are exactly `input_schema`, `result_schema`, and
`command_id`. Aggregation keys are exactly `input_schemas`, `result_schema`, and
`command_id`.

### `input_index`

```yaml
input_index:
  parity: [inputs/parity/imagefont.json]
  coverage: [inputs/coverage/imagefont.json]
  benchmark: [inputs/benchmark/imagefont.json]
```

Each array is unique. Every indexed file exists, stays beneath its lane root,
and is indexed once. Every discovered active input JSON is indexed.

### `coverage_components`

Code coverage is many-to-many: several operations may map to one component and
one operation may map to several files. Declare reusable components:

```yaml
coverage_components:
  - id: imagefont-core
    target_profile: rust-cpu
    paths:
      - pillow-rs/src/font.rs
      - pillow-rs/src/imagefont.rs
    dimensions: [function, line, branch, region]
    thresholds:
      - dimension: line
        minimum_percent: 100
      - dimension: branch
        minimum_percent: 100
```

Exact component keys are `id`, `target_profile`, `paths`, `dimensions`, and
`thresholds`. A threshold has exact `dimension` and `minimum_percent` keys.
Fixed dimensions are `function`, `line`, `branch`, and `region`.

### `documentation`

```yaml
documentation:
  command_id: docs
  specification_outputs:
    - docs/generated/public-contract.md
  evidence_outputs:
    - docs/generated/parity-status.md
    - docs/generated/coverage-status.md
    - docs/generated/benchmark-status.md
```

These are generated destinations, not evidence sources.

## 4. Public surfaces and operations

### Surface

Exact keys are `id`, `kind`, `source_path`, `storage_slug`, and `operations`:

```yaml
- id: PIL.ImageFont.FreeTypeFont
  kind: type
  source_path: PIL.ImageFont.FreeTypeFont
  storage_slug: imagefont-freetypefont
  operations: []
```

Surface kinds are:

```text
namespace type format abi cli protocol service
```

### Operation

Every operation has exact keys:

```yaml
- id: getbbox
  kind: method
  classification: endpoint
  lifecycle:
    status: current
  source: {}
  targets: []
  requirements: []
  parity: {}
  coverage: {}
  benchmark: {}
```

Operation kinds are:

```text
function method constructor property_get property_set command abi_function
protocol_operation format_operation constant type enum enum_variant flag macro
record tag error namespace
```

`classification` is `endpoint` for independently observable public behavior
and `non_endpoint` only for an inventoried name with no independent public
observation. Constants, public layouts, error values, and compile-visible
symbols can be endpoints.

Lifecycle is either:

```yaml
lifecycle:
  status: current
```

or:

```yaml
lifecycle:
  status: deprecated
  authority: public deprecation source
  replacement: replacement-symbol-or-null
```

### Source binding

Exact keys are `oracle_id`, `path`, `signature`, `parameters`, and `result`:

```yaml
source:
  oracle_id: pillow
  path: PIL.ImageFont.FreeTypeFont.getbbox
  signature: "getbbox(text, mode='', direction=None, ...)"
  parameters:
    - id: text
      style: positional_or_keyword
      value_types: [string]
      omission:
        kind: required
    - id: mode
      style: positional_or_keyword
      value_types: [string]
      omission:
        kind: literal
        value: ""
  result:
    shape: sequence
    observations:
      - path: value
        value_types: [sequence]
        comparison:
          kind: exact
    error:
      fields: [class, kind, message, stage, code]
      message:
        mode: normalized
        transforms: [strip_runtime_addresses]
        reason: Runtime object addresses are not public behavior
```

Parameter styles are:

```text
receiver positional positional_or_keyword keyword variadic_positional
variadic_keyword input_asset stdin environment option
```

Value types are:

```text
null boolean integer number string bytes path enum sequence mapping record
image font stream handle any_json
```

Parameter keys are exactly `id`, `style`, `value_types`, and `omission`.
`value_types` is a non-empty unique array from the fixed type vocabulary. It
represents public unions directly, for example `[string, bytes, null]`, rather
than falling back to a custom schema.
`omission` is exactly one fixed variant:

```json
{"kind": "required"}
{"kind": "literal", "value": null}
{"kind": "sentinel", "name": "DEFAULT", "semantics": "Use runtime default layout"}
```

A literal default must match at least one declared value type. A sentinel records a public
non-JSON default by stable name and semantics; it is not an extension hook.
Receivers use `required`. Variadic parameters use an appropriate literal empty
sequence or mapping.

The `parameters` array is the fixed typed parameter table for the public
operation. Parameter IDs preserve source spelling, including legitimate names
such as `expected`, `status`, `output`, or `error`; the schema defines their
structure instead of blacklisting words. It is not a runtime extension schema.
Parity workflow arguments must reference declared parameter IDs, supply every
parameter whose omission kind is `required`, and match one declared value type.

Result shapes are:

```text
none scalar sequence mapping record bytes image mask encoded_file metrics
handle iterator stream cli protocol filesystem
```

Observation comparison is one exact discriminated object:

```json
{"kind": "exact"}
{"kind": "ordered"}
{"kind": "unordered"}
{"kind": "bytes"}
{"kind": "numeric", "absolute_tolerance": 0, "relative_tolerance": 0, "nan_policy": "forbidden"}
{"kind": "text", "transforms": ["normalize_newlines"], "reason": "Public contract is platform-neutral text"}
{"kind": "image", "pixel_mode": "exact", "maximum_channel_delta": 0, "metadata_mode": "exact", "reason": null}
{"kind": "filesystem", "path_mode": "relative", "ordering": "sorted", "content_mode": "exact"}
```

Numeric tolerances are non-negative and the NaN policy is `forbidden`, `equal`,
or `unequal`. Text transforms are a unique subset of
`normalize_newlines`, `normalize_path_separators`,
`strip_runtime_addresses`, and `unicode_nfc`; transforms require a reason.
Image pixels are `exact` with zero delta or `bounded_delta` with a positive
maximum channel delta. Metadata mode is `exact`, `declared_only`, or `ignored`;
every relaxation requires a reason. Filesystem content is always exact.

There is no free-form `semantic` comparator. For nondeterministic encoded
output, run public inspect/verify/decode steps in the same independent workflow
and compare their stable observations.

Error keys are exactly `fields` and `message`. Error fields are `class`, `kind`,
`message`, `stage`, and `code`. Message keys are exactly `mode`, `transforms`,
and `reason`. Mode is `exact`, `normalized`, or `ignored`; normalized messages
require explicit transforms and a reason, ignored messages require a reason,
ignored and exact messages require an empty transform array, and exact messages
require null reason. Expected messages do not belong here.

### Target binding and support

Each operation has one target binding per target:

```yaml
targets:
  - target_id: pillow-rs-core
    path: pillow_rs::FreeTypeFont::getbbox
    signature: "getbbox(&self, text: &str, ...) -> Result<...>"
    support:
      status: partial
      reason: Complex text shaping is not implemented
      missing_requirements:
        - PIL.ImageFont.FreeTypeFont.getbbox.shaping.complex
```

Exact binding keys are `target_id`, `path`, `signature`, and `support`.
`supported` and `partial` bindings require non-null `path` and `signature`.
Bindings that claim no target endpoint (`unimplemented`,
`intentionally_unsupported`, `out_of_scope`, or `not_applicable`) require a
null `signature`; `path` may name the planned/mapped public identity or be null.

Support statuses:

- `supported` — claims the complete declared contract;
- `partial` — requires `reason` and non-empty `missing_requirements`;
- `unimplemented` — requires `reason` and `blocker`;
- `intentionally_unsupported` — requires `reason` and `authority`;
- `out_of_scope` — requires `reason` and `authority`;
- `not_applicable` — allowed only for a non-endpoint.

Support is per target, not per target profile. Profile-specific behavior is
expressed by requirements and lane profile selection.

## 5. Requirements and lane policy

Requirements are the semantic join between the manifest, all three input
interfaces, results, aggregation, and documentation:

```yaml
requirements:
  - id: PIL.ImageFont.FreeTypeFont.getbbox.text.basic-latin
    dimension: input_family
    description: Basic Latin text through the public method
    lanes: [parity, coverage]
    target_profiles: [rust-cpu]
```

Exact requirement keys are `id`, `dimension`, `description`, `lanes`,
`target_profiles`, and optional `budget`.

Requirement dimensions:

```text
parameter parameter_combination input_family success_path error_path mode
format protocol_variant abi_variant asset_family boundary backend runtime
feature historical_divergence code_path performance documentation
```

Performance budgets are manifest policy:

```yaml
budget:
  kind: relative
  metric: latency
  statistic: median
  operator: less_than_or_equal
  value: 1.10
  unit: ratio
  baseline_subject: freetype-c
```

Exact budget keys are `kind`, `metric`, `statistic`, `operator`, `value`,
`unit`, and `baseline_subject`. `kind` is `absolute` or `relative`.
`baseline_subject` is null for absolute budgets and an oracle or target-profile
ID for relative budgets.

Statistics are `min`, `median`, `mean`, `p95`, `p99`, `max`, `total`, and
`weighted_mean`. Operators are `less_than_or_equal` and
`greater_than_or_equal`.

Each operation declares all three lane policies. A required lane uses:

```yaml
parity:
  applicability: required
  target_profiles: [rust-cpu]

coverage:
  applicability: required
  target_profiles: [rust-cpu]
  component_ids: [imagefont-core]

benchmark:
  applicability: required
  target_profiles: [rust-cpu]
  metrics: [latency, throughput]
```

A non-applicable lane uses exactly:

```yaml
benchmark:
  applicability: not_applicable
  reason: Compile-time type alias has no meaningful runtime workload
```

Benchmark metrics are:

```text
latency throughput allocations peak_memory resident_memory artifact_size
encoded_size startup_time cpu_time
```

Every required lane has at least one requirement for each named profile. Every
such requirement maps to at least one input item. `not_applicable` lanes have
no requirements or inputs.

## 6. Parity input interface

Parity input documents have exactly `schema` and `cases`:

```json
{
  "schema": "migration-parity/parity-input@1",
  "cases": [
    {
      "case_id": "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin",
      "surface": "PIL.ImageFont.FreeTypeFont",
      "operation": "getbbox",
      "covers": [
        "PIL.ImageFont.FreeTypeFont.getbbox.text.basic-latin"
      ],
      "target_profiles": ["rust-cpu"],
      "assets": [
        {
          "id": "font",
          "kind": "ref",
          "path": "fonts/DejaVuSans.ttf",
          "sha256": "64-lowercase-hex",
          "media_type": "font/ttf"
        }
      ],
      "steps": [
        {
          "step_id": "load",
          "surface": "PIL.ImageFont",
          "operation": "truetype",
          "receiver": null,
          "arguments": {
            "font": {"kind": "asset", "asset_id": "font"},
            "size": {"kind": "literal", "value": 20}
          }
        },
        {
          "step_id": "bbox",
          "surface": "PIL.ImageFont.FreeTypeFont",
          "operation": "getbbox",
          "receiver": {"kind": "binding", "step_id": "load"},
          "arguments": {
            "text": {"kind": "literal", "value": "Hello"}
          }
        }
      ],
      "observations": ["bbox"]
    }
  ]
}
```

Case keys are exactly `case_id`, `surface`, `operation`, `covers`,
`target_profiles`, `assets`, `steps`, and `observations`.
`surface` and `operation` identify the primary operation and form the stable
case-ID prefix. `covers` may name requirements from several operations in the
workflow, but every covered operation must have an observed step and the
primary operation must be observed.

Step keys are exactly `step_id`, `surface`, `operation`, `receiver`, and
`arguments`. Steps call manifest operations; they do not name
runner-specific dispatcher operations. `receiver` is null or a value
descriptor. `arguments` keys are validated against the called operation's
parameter table. Later steps refer to an earlier step result by `step_id`.

`observations` names the public step results compared between the live oracle
and target. Setup steps may be unobserved but remain public calls. This fixed
workflow model supports constructors and methods, ABI handle lifetimes,
detect/inspect/verify/decode pipelines, CLI preparation, and simple one-call
cases. One shared asset workflow can therefore cover several public operations
without embedding or duplicating outputs.

The oracle and each target receive the same input workflow independently.
Inputs never receive or reference generated source/target output.

## 7. Coverage input interface

Coverage input documents have exactly `schema` and `plans`:

```json
{
  "schema": "migration-parity/coverage-input@1",
  "plans": [
    {
      "plan_id": "imagefont.public-paths",
      "covers": [
        "PIL.ImageFont.FreeTypeFont.getbbox.text.basic-latin"
      ],
      "target_profile": "rust-cpu",
      "selectors": {
        "parity_case_ids": [
          "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin"
        ],
        "command_ids": []
      },
      "component_ids": ["imagefont-core"],
      "command_id": "coverage"
    }
  ]
}
```

Plan keys are exactly `plan_id`, `covers`, `target_profile`, `selectors`,
`component_ids`, and `command_id`. Selector keys are exactly
`parity_case_ids` and `command_ids`; at least one selector is required.

Command IDs resolve through the manifest command registry. This avoids an
unverifiable free-form repository-test ID registry. Coverage-only internal
commands may satisfy coverage requirements but never parity requirements.
When a plan selects only parity cases, every covered requirement must be
covered by at least one selected case. A selected command is a maintained
executable assertion by the plan; runner/command audits must verify that
assertion rather than trusting a second inventory.

Plans may cover several operations and components. Coverage is not forced into
a false one-operation/one-file model.

## 8. Benchmark input interface

Benchmark documents have exactly `schema`, `workloads`, and `suites`:

```json
{
  "schema": "migration-parity/benchmark-input@1",
  "workloads": [
    {
      "workload_id": "imagefont.getbbox.standard-latin",
      "covers": [
        "PIL.ImageFont.FreeTypeFont.getbbox.performance.standard"
      ],
      "subjects": [
        {"kind": "oracle", "id": "pillow"},
        {"kind": "target_profile", "id": "rust-cpu"}
      ],
      "input": {
        "kind": "parity_case",
        "case_id": "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin"
      },
      "measurement": {
        "boundary": "observed_steps",
        "step_ids": ["bbox"],
        "metrics": ["latency", "throughput"],
        "warmup_iterations": 20,
        "measurement_iterations": 100,
        "samples": 30,
        "concurrency": 1,
        "cache_state": "warm",
        "correctness_gate": "parity_pass"
      }
    }
  ],
  "suites": [
    {
      "suite_id": "interactive-text",
      "description": "Weighted interactive text workload",
      "members": [
        {
          "workload_id": "imagefont.getbbox.standard-latin",
          "weight": 30
        }
      ]
    }
  ]
}
```

Workload keys are exactly `workload_id`, `covers`, `subjects`, `input`, and
`measurement`. A subject has exact `kind` and `id` keys; kind is `oracle` or
`target_profile`.

`input` is exactly one fixed variant:

- `{"kind":"parity_case","case_id":"..."}`;
- `{"kind":"workflow","assets":[],"steps":[],"observations":[]}`;
- `{"kind":"command","command_id":"..."}`;
- `{"kind":"artifact","path":"repository-relative-path"}`.

Workflow fields use the same asset, step, and observation interfaces as parity
cases.

Measurement boundaries are `observed_steps`, `whole_workflow`, `process`, and
`artifact`. Cache state is `cold`, `warm`, or `mixed`. Correctness gates are
`parity_pass`, `source_target_match`, `successful_execution`, and
`not_applicable`. `not_applicable` is valid only for non-behavioral artifact
measurements.

A parity-case workload may cover only requirements covered by that case.
Workflow-backed requirements must belong to operations inside the declared
measurement boundary. Process-command and artifact workloads bind requirements
through their maintained input declaration and are verified by their runner
and correctness gate.

Suite keys are exactly `suite_id`, `description`, and `members`. Members have
exact `workload_id` and positive `weight` fields. Suites model weighted
real-world profiles without putting measurements in the manifest.

## 9. Asset and value interfaces

Value descriptors are exact discriminated objects:

```json
{"kind": "literal", "value": "Hello"}
{"kind": "asset", "asset_id": "font"}
{"kind": "binding", "step_id": "load"}
```

Literal values may be any JSON value, but the argument name and value type must
match the operation parameter table. This permits legitimate public parameters
named `status`, `output`, `expected`, or `error`; recursively banning words
inside public input data is invalid.

Asset variants:

| Kind | Exact fields |
| --- | --- |
| `ref` | `id`, `kind`, `path`, `sha256`, `media_type` |
| `inline` | `id`, `kind`, `encoding`, `data`, `sha256`, `media_type` |
| `generated` | `id`, `kind`, `path`, `command_id`, `seed`, `sha256`, `media_type` |
| `builtin` | `id`, `kind`, `name` |
| `missing` | `id`, `kind`, `path` |
| `remote_mock` | `id`, `kind`, `path`, `command_id`, `endpoint`, `sha256`, `media_type` |

`encoding` is `base64` or `utf8`. Paths are repository-relative and cannot
traverse. Input digests are allowed and encouraged: they identify stimulus
bytes. Expected output digests remain forbidden.

Generated assets require a deterministic command and seed. `remote_mock`
describes a deterministic local mock; live network access is allowed only when
the network itself is the public contract.

## 10. Completeness and evolution

Report these dimensions separately:

1. public inventory represented / authoritative public inventory;
2. endpoints with complete operation contracts / declared endpoints;
3. parity requirements mapped / parity requirements;
4. coverage requirements mapped / coverage requirements;
5. benchmark requirements mapped / benchmark requirements;
6. parity comparisons passing / executed comparisons, with run identity;
7. covered/total for each code dimension, with snapshot identity;
8. workloads meeting budgets / measured workloads, with run and environment;
9. fresh generated pages / declared pages.

Never write bare “100%.”

`@2` is fixed. Improve it only by:

1. defining the missing concept and invariant;
2. assigning a new schema identifier when accepted shape or meaning changes;
3. updating manifest, input, result, aggregation, validation, examples, and
   documentation consumers together;
4. providing a deterministic maintained migrator;
5. testing valid old/new documents and intentional invalid cases;
6. rejecting mixed-version joins.

Do not add extension maps, plugin-defined fields, arbitrary schemas, or
catch-all metadata to avoid a versioned contract change.
