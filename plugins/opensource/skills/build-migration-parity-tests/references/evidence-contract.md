# Evidence, Aggregation, and Documentation Contract

This file is normative for generated parity, coverage, benchmark, aggregate,
and documentation artifacts. Read it with
[the manifest and input contract](manifest-contract.md).

Unknown fields are errors. Results are immutable observations from a run; they
never become manifest or input truth.

## Contents

- 1. Shared identity
- 2. Public workflow result
- 3. Parity result
- 4. Coverage result
- 5. Benchmark result
- 6. Aggregate status
- 7. Documentation
- 8. Compatibility and failure rules

## 1. Shared identity

Every lane result has an exact identity object:

```json
{
  "run_id": "durable-id",
  "started_at": "RFC3339",
  "finished_at": "RFC3339",
  "manifest": {
    "path": "tests/fixtures/manifest.yaml",
    "schema": "migration-parity/manifest@2",
    "sha256": "64-lowercase-hex"
  },
  "inputs": [
    {
      "path": "tests/fixtures/inputs/parity/imagefont.json",
      "schema": "migration-parity/parity-input@1",
      "sha256": "64-lowercase-hex"
    }
  ],
  "assets": [
    {
      "input_path": "tests/fixtures/inputs/parity/imagefont.json",
      "item_id": "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin",
      "asset_id": "font",
      "kind": "ref",
      "locator": "fonts/DejaVuSans.ttf",
      "sha256": "64-lowercase-hex"
    }
  ],
  "oracles": [
    {
      "oracle_id": "pillow",
      "name": "Pillow",
      "version": "12.2.0",
      "runtime": "CPython 3.12"
    }
  ],
  "targets": [
    {
      "target_profile": "rust-cpu",
      "target_id": "pillow-rs-core",
      "revision": "immutable-vcs-or-build-id",
      "dirty": false,
      "runtime": "rustc exact version",
      "backend": "cpu",
      "features": ["default"]
    }
  ],
  "command": {
    "command_id": "parity",
    "argv": ["make", "migration-parity-test"],
    "cwd": ".",
    "timeout_seconds": 900
  }
}
```

Identity keys are exactly `run_id`, `started_at`, `finished_at`, `manifest`,
`inputs`, `assets`, `oracles`, `targets`, and `command`.

Nested exact keys:

| Object | Keys |
| --- | --- |
| manifest | `path`, `schema`, `sha256` |
| input | `path`, `schema`, `sha256` |
| asset | `input_path`, `item_id`, `asset_id`, `kind`, `locator`, `sha256` |
| oracle | `oracle_id`, `name`, `version`, `runtime` |
| target | `target_profile`, `target_id`, `revision`, `dirty`, `runtime`, `backend`, `features` |
| command | `command_id`, `argv`, `cwd`, `timeout_seconds` |

Input digests cover exactly the manifest-indexed files selected by the result.
Asset entries cover every selected workflow asset. `locator` is its
repository-relative path, built-in name, or null for inline data; `sha256` is
the verified stimulus digest or null only when the input variant has no bytes
to hash.
Behavior-relevant non-secret environment belongs in the lane-specific result.

Infrastructure errors use exactly:

```json
{
  "scope": "oracle|target|collector|runner|artifact|aggregation",
  "id": "affected-id-or-null",
  "kind": "stable-machine-kind",
  "message": "bounded-diagnostic-message"
}
```

An adapter startup failure, timeout, crash, malformed transport, missing ID,
extra ID, or count mismatch is infrastructure failure. It is not a public
target error.

## 2. Public workflow result

Parity source and target adapters emit one workflow result for every selected
case:

```json
{
  "case_id": "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin",
  "status": "completed",
  "observations": [
    {
      "step_id": "bbox",
      "status": "ok",
      "value": [0, 4, 46, 19]
    }
  ]
}
```

or:

```json
{
  "case_id": "PIL.ImageFont.FreeTypeFont.getbbox.invalid-direction",
  "status": "completed",
  "observations": [
    {
      "step_id": "bbox",
      "status": "error",
      "error": {
        "class": "ValueError",
        "kind": "invalid_argument",
        "message": "stable public message",
        "stage": "layout",
        "code": null
      }
    }
  ]
}
```

Workflow-result keys are exactly `case_id`, `status`, and `observations`.
Workflow status is `completed` or `not_run`. Observation keys are:

- success: exactly `step_id`, `status`, and `value`;
- public error: exactly `step_id`, `status`, and `error`;
- not run: exactly `step_id`, `status`, and `reason`.

Observation status is `ok`, `error`, or `not_run`. Public-error keys are exactly
`class`, `kind`, `message`, `stage`, and `code`; nullable values remain present.

Large byte/image values may externalize the diagnostic copy:

```json
{
  "artifact_ref": "run-relative/path",
  "length": 49152,
  "sha256": "diagnostic-digest"
}
```

Exact comparison occurs on the raw value before externalization. A digest is
diagnostic evidence, never a substitute for raw comparison when raw values are
available.

## 3. Parity result

Schema: `migration-parity/parity-result@1`.

Exact top-level keys:

```json
{
  "schema": "migration-parity/parity-result@1",
  "identity": {},
  "status": "completed",
  "summary": {},
  "comparisons": [],
  "infrastructure_errors": []
}
```

Artifact status is `completed`, `infrastructure_failed`, `cancelled`, or
`invalid`.

Summary keys are exactly:

```json
{
  "selected": 2,
  "executed": 2,
  "passed": 1,
  "failed": 1,
  "not_run": 0,
  "infrastructure_errors": 0
}
```

There is one comparison for every selected case/target-profile pair:

```json
{
  "case_id": "PIL.ImageFont.FreeTypeFont.getbbox.basic-latin",
  "target_profile": "rust-cpu",
  "requirements": [
    "PIL.ImageFont.FreeTypeFont.getbbox.text.basic-latin"
  ],
  "source": {},
  "target": {},
  "outcome": "pass",
  "diffs": []
}
```

Comparison keys are exactly `case_id`, `target_profile`, `requirements`,
`source`, `target`, `outcome`, and `diffs`. Source and target are workflow
results. Outcome is `pass`, `fail`, or `not_run`.

A diff has exact keys:

```json
{
  "step_id": "bbox",
  "path": "value[2]",
  "kind": "value_mismatch",
  "source": 46,
  "target": 45,
  "message": "exact integer mismatch"
}
```

The comparator first matches case and observation ID sets, then public status,
then declared observations. Truth table:

| Source | Target | Outcome |
| --- | --- | --- |
| ok and equal | ok and equal | pass |
| ok | different ok | fail |
| ok | error | fail |
| error | ok | fail |
| equal public error | equal public error | pass |
| different public error | different public error | fail |

Do not accept “any error,” ignore undeclared mismatches, use case-specific
success logic, or reuse target output as source output.

## 4. Coverage result

Schema: `migration-parity/coverage-result@1`.

Exact top-level keys:

```json
{
  "schema": "migration-parity/coverage-result@1",
  "identity": {},
  "status": "completed",
  "collector": {},
  "summary": {},
  "plans": [],
  "infrastructure_errors": []
}
```

Artifact status is `completed`, `infrastructure_failed`, `cancelled`, `invalid`,
or `not_ingested`.

Collector keys are exactly `name`, `version`, `snapshot_id`, and
`artifact_ingested`.

Summary keys are exactly:

```json
{
  "plans_selected": 1,
  "plans_executed": 1,
  "plans_not_run": 0,
  "tests_passed": 12,
  "tests_failed": 0
}
```

Plan result:

```json
{
  "plan_id": "imagefont.public-paths",
  "target_profile": "rust-cpu",
  "requirements": [],
  "selected": {
    "parity_case_ids": [],
    "command_ids": []
  },
  "execution": {
    "status": "completed",
    "tests_passed": 12,
    "tests_failed": 0
  },
  "components": [
    {
      "component_id": "imagefont-core",
      "files": [
        {
          "path": "pillow-rs/src/font.rs",
          "dimensions": [
            {
              "dimension": "line",
              "covered": 90,
              "total": 100,
              "uncovered": ["repository-native-location"]
            }
          ]
        }
      ],
      "thresholds": [
        {
          "dimension": "line",
          "minimum_percent": 100,
          "covered": 90,
          "total": 100,
          "outcome": "fail"
        }
      ]
    }
  ]
}
```

Plan keys are exactly `plan_id`, `target_profile`, `requirements`, `selected`,
`execution`, and `components`. Nested exact keys:

| Object | Keys |
| --- | --- |
| selected | `parity_case_ids`, `command_ids` |
| execution | `status`, `tests_passed`, `tests_failed` |
| component | `component_id`, `files`, `thresholds` |
| file | `path`, `dimensions` |
| dimension | `dimension`, `covered`, `total`, `uncovered` |
| threshold | `dimension`, `minimum_percent`, `covered`, `total`, `outcome` |

Execution status is `completed`, `failed`, or `not_run`. Threshold outcome is
`pass`, `fail`, or `not_proven`. Always store integer covered and total counts;
percentages are presentation.

Coverage proves only the selected target profile, files, dimensions, and
snapshot. It does not prove parity.

## 5. Benchmark result

Schema: `migration-parity/benchmark-result@1`.

Exact top-level keys:

```json
{
  "schema": "migration-parity/benchmark-result@1",
  "identity": {},
  "status": "completed",
  "environment": {},
  "summary": {},
  "workloads": [],
  "suites": [],
  "infrastructure_errors": []
}
```

Artifact status is `completed`, `infrastructure_failed`, `cancelled`, or
`invalid`.

Environment keys are exactly:

```json
{
  "machine_id": "stable-non-secret-id",
  "os": "exact",
  "architecture": "exact",
  "cpu": "exact",
  "memory_bytes": 0,
  "power_mode": "exact-or-unknown",
  "toolchain": "exact"
}
```

Summary keys are exactly:

```json
{
  "workloads_selected": 1,
  "workloads_measured": 1,
  "workloads_not_run": 0,
  "budgets_passed": 1,
  "budgets_failed": 0,
  "budgets_not_proven": 0
}
```

Workload result:

```json
{
  "workload_id": "imagefont.getbbox.standard-latin",
  "requirements": [],
  "measurement_policy": {},
  "correctness": {
    "gate": "parity_pass",
    "outcome": "pass",
    "evidence_id": "parity-run-id"
  },
  "subjects": [
    {
      "kind": "target_profile",
      "id": "rust-cpu",
      "status": "completed",
      "measurements": [
        {
          "metric": "latency",
          "unit": "millisecond",
          "sample_count": 30,
          "statistics": {
            "min": 1.1,
            "median": 1.3,
            "mean": 1.31,
            "p95": 1.5,
            "p99": 1.6,
            "max": 1.7,
            "total": null,
            "weighted_mean": null,
            "standard_deviation": 0.08
          },
          "raw_samples_ref": "run-relative-path-or-null"
        }
      ]
    }
  ],
  "budgets": [
    {
      "requirement_id": "requirement-id",
      "subject_id": "rust-cpu",
      "baseline_subject": "pillow",
      "metric": "latency",
      "statistic": "median",
      "operator": "less_than_or_equal",
      "required": 1.1,
      "observed": 0.95,
      "unit": "ratio",
      "outcome": "pass"
    }
  ]
}
```

Workload keys are exactly `workload_id`, `requirements`,
`measurement_policy`, `correctness`, `subjects`, and `budgets`.
`measurement_policy` copies the input measurement object exactly.

Correctness keys are exactly `gate`, `outcome`, and `evidence_id`; outcome is
`pass`, `fail`, or `not_proven`. A performance budget is `not_proven` when its
correctness gate is not passing.

Subject keys are exactly `kind`, `id`, `status`, and `measurements`. Status is
`completed`, `failed`, or `not_run`.

Measurement keys are exactly `metric`, `unit`, `sample_count`, `statistics`,
and `raw_samples_ref`. Statistics always contains `min`, `median`, `mean`,
`p95`, `p99`, `max`, `total`, `weighted_mean`, and `standard_deviation`, with
null for inapplicable statistics.

Budget-result keys are exactly `requirement_id`, `subject_id`,
`baseline_subject`, `metric`, `statistic`, `operator`, `required`, `observed`,
`unit`, and `outcome`.

Suite results have this fixed shape:

```json
{
  "suite_id": "interactive-text",
  "members": [
    {"workload_id": "imagefont.getbbox.standard-latin", "weight": 30}
  ],
  "subjects": [
    {
      "kind": "target_profile",
      "id": "rust-cpu",
      "status": "completed",
      "measurements": [
        {"metric": "latency", "unit": "millisecond", "weighted_mean": 1.3}
      ]
    }
  ],
  "comparisons": [
    {
      "baseline_subject": "pillow",
      "subject_id": "rust-cpu",
      "metric": "latency",
      "baseline_value": 1.5,
      "subject_value": 1.3,
      "unit": "millisecond",
      "ratio": 0.8666666667
    }
  ]
}
```

Suite keys are exactly `suite_id`, `members`, `subjects`, and `comparisons`.
Member keys are exactly `workload_id` and `weight`. Suite-subject keys are
exactly `kind`, `id`, `status`, and `measurements`. Suite measurement keys are
exactly `metric`, `unit`, and `weighted_mean`. Suite-comparison keys are
exactly `baseline_subject`, `subject_id`, `metric`, `baseline_value`,
`subject_value`, `unit`, and `ratio`. Null is used when a compatible weighted
value or comparison cannot be computed. Suites use input weights and current
compatible workload measurements; they do not mutate input suites or create
new budget outcomes.

Never compare benchmark baselines across incompatible workload, manifest,
input, target configuration, or machine identity.

## 6. Aggregate status

Schema: `migration-parity/status-report@1`.

Exact top-level keys:

```json
{
  "schema": "migration-parity/status-report@1",
  "manifest": {
    "path": "tests/fixtures/manifest.yaml",
    "schema": "migration-parity/manifest@2",
    "sha256": "hex"
  },
  "target_profiles": [],
  "evidence": [],
  "completeness": [],
  "operations": [],
  "stale_or_incompatible_evidence": []
}
```

Target-profile identity uses the shared target identity shape. Evidence entries
have exact `lane`, `run_id`, and `snapshot_id` keys; `snapshot_id` is null
outside coverage.

Completeness entries have exact keys:

```json
{
  "dimension": "parity_input_mapping",
  "target_profile": "rust-cpu-or-null",
  "numerator": 10,
  "denominator": 12,
  "evidence_id": "run-or-snapshot-id-or-null"
}
```

Fixed completeness dimensions:

```text
inventory_representation operation_contracts parity_input_mapping
coverage_input_mapping benchmark_input_mapping parity_outcome function_coverage
line_coverage branch_coverage region_coverage benchmark_budget_outcome
documentation_freshness
```

Operation status entries have exact keys:

```json
{
  "surface": "PIL.ImageFont.FreeTypeFont",
  "operation": "getbbox",
  "target_profile": "rust-cpu",
  "classification": "endpoint",
  "support": "partial",
  "requirements": [],
  "parity": {},
  "coverage": {},
  "benchmark": {}
}
```

Lane summaries use exact `applicability`, `input_ids`, `outcome`,
`evidence_id`, and `details` keys. Outcome is `pass`, `fail`, `not_run`,
`not_proven`, or `not_applicable`. `details` is a fixed array of diagnostic
strings, not a dynamic result object.

Stale/incompatible entries have exact `lane`, `run_id`, `reason`, and
`identity_diff` keys. `identity_diff` is an array of stable differing identity
paths.

The aggregate derives all denominators from the current manifest and input
index. It never trusts stored percentages or a parallel inventory.

## 7. Documentation

Generate two layers:

1. specification reference from manifest plus indexed inputs;
2. current evidence status from a compatible aggregate.

Every generated page records:

- generator and schema version;
- manifest path, schema, and digest;
- target profile and immutable revision when evidence is shown;
- parity run, coverage run/snapshot, and benchmark run IDs;
- whether each statement is `declared`, `measured`, `not_proven`, or
  `stale/incompatible`.

Documentation generation is deterministic for the same inputs. CI regenerates
and diffs checked-in pages or publishes immutable generated artifacts.
Documentation never becomes input truth.

## 8. Compatibility and failure rules

Join evidence only when:

- manifest path, schema, and digest match;
- every claimed input path, schema, and digest matches;
- target profile, target ID, immutable revision, runtime, backend, and features
  match the requested view;
- source identity matches for parity;
- coverage collector and snapshot are fresh and ingested;
- benchmark workload, measurement policy, machine, and environment are
  compatible for the claimed comparison.

Mark missing, stale, cancelled, invalid, infrastructure-failed, dirty-target,
or incompatible evidence `not_proven`. A result with any `target.dirty: true`
is never current proof.

Fail validation or ingestion on:

- unknown fields or unsupported schema IDs;
- selected/returned ID-set disagreement;
- a result naming an unindexed case, plan, workload, suite, operation,
  requirement, component, command, oracle, target, or profile;
- malformed workflow observations or duplicate IDs;
- infrastructure errors counted as public target errors;
- coverage percentages without integer covered/total counts;
- coverage without a fresh ingested snapshot;
- benchmark measurements without environment and policy identity;
- budget pass with a failed or unproven correctness gate;
- incompatible lane artifacts joined into one status;
- docs presenting missing/stale evidence as passing.
