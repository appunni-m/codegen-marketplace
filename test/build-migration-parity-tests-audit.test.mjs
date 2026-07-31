import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const script = path.resolve(
  'plugins/opensource/skills/build-migration-parity-tests/scripts/audit_parity_fixtures.py',
);

async function fixture(files) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'migration-parity-'));
  await Promise.all(
    Object.entries(files).map(async ([relativePath, contents]) => {
      const destination = path.join(root, relativePath);
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.writeFile(destination, contents);
    }),
  );
  return root;
}

function audit(root, ...args) {
  return spawnSync(
    'python3',
    ['-B', script, root, '--format', 'json', ...args],
    { encoding: 'utf8' },
  );
}

function command(id) {
  return {
    id,
    argv: ['make', id],
    cwd: '.',
    timeout_seconds: 60,
  };
}

function validContract() {
  const assetBytes = 'fixture bytes';
  const assetDigest = createHash('sha256').update(assetBytes).digest('hex');
  const requirement = 'Parser.parse.text-and-performance';
  const caseId = 'Parser.parse.legitimate-expected-parameter';

  const manifest = {
    schema: 'migration-parity/manifest@2',
    scope: {
      id: 'parser-contract',
      mode: 'full',
      inventory: {
        authority: 'public parser API',
        revision: 'legacy-1.0.0',
        command_id: 'inventory',
      },
    },
    oracles: [
      {
        id: 'legacy',
        name: 'Legacy parser',
        version: '1.0.0',
        runtime: 'legacy runtime',
        identity_command_id: 'oracle-identity',
        contract: 'Public parse behavior',
        components: [],
      },
    ],
    targets: [
      {
        id: 'new-parser',
        name: 'New parser',
        runtime: 'public library',
        identity_command_id: 'target-identity',
        contract: 'Public parse behavior',
      },
    ],
    target_profiles: [
      {
        id: 'native',
        target_id: 'new-parser',
        backend: 'cpu',
        features: ['default'],
      },
    ],
    commands: [
      'inventory',
      'oracle-identity',
      'target-identity',
      'parity',
      'coverage',
      'benchmark',
      'aggregate',
      'docs',
    ].map(command),
    interfaces: {
      parity: {
        input_schema: 'migration-parity/parity-input@1',
        result_schema: 'migration-parity/parity-result@1',
        command_id: 'parity',
      },
      coverage: {
        input_schema: 'migration-parity/coverage-input@1',
        result_schema: 'migration-parity/coverage-result@1',
        command_id: 'coverage',
      },
      benchmark: {
        input_schema: 'migration-parity/benchmark-input@1',
        result_schema: 'migration-parity/benchmark-result@1',
        command_id: 'benchmark',
      },
      aggregation: {
        input_schemas: [
          'migration-parity/parity-result@1',
          'migration-parity/coverage-result@1',
          'migration-parity/benchmark-result@1',
        ],
        result_schema: 'migration-parity/status-report@1',
        command_id: 'aggregate',
      },
    },
    input_index: {
      parity: ['inputs/parity/parser.json'],
      coverage: ['inputs/coverage/parser.json'],
      benchmark: ['inputs/benchmark/parser.json'],
    },
    coverage_components: [
      {
        id: 'parser-core',
        target_profile: 'native',
        paths: ['src/parser.rs'],
        dimensions: ['function', 'line', 'branch', 'region'],
        thresholds: [
          { dimension: 'line', minimum_percent: 100 },
          { dimension: 'branch', minimum_percent: 100 },
        ],
      },
    ],
    surfaces: [
      {
        id: 'Parser',
        kind: 'namespace',
        source_path: 'legacy.Parser',
        storage_slug: 'parser',
        operations: [
          {
            id: 'parse',
            kind: 'function',
            classification: 'endpoint',
            lifecycle: { status: 'current' },
            source: {
              oracle_id: 'legacy',
              path: 'legacy.Parser.parse',
              signature: "parse(text, expected='', sample=None)",
              parameters: [
                {
                  id: 'text',
                  style: 'positional_or_keyword',
                  value_types: ['string'],
                  omission: { kind: 'required' },
                },
                {
                  id: 'expected',
                  style: 'keyword',
                  value_types: ['string'],
                  omission: { kind: 'literal', value: '' },
                },
                {
                  id: 'sample',
                  style: 'input_asset',
                  value_types: ['bytes', 'null'],
                  omission: {
                    kind: 'sentinel',
                    name: 'NO_SAMPLE',
                    semantics: 'Parse without an attached binary sample',
                  },
                },
              ],
              result: {
                shape: 'scalar',
                observations: [
                  {
                    path: 'value',
                    value_types: ['string'],
                    comparison: { kind: 'exact' },
                  },
                ],
                error: {
                  fields: ['class', 'kind', 'message', 'stage', 'code'],
                  message: {
                    mode: 'exact',
                    transforms: [],
                    reason: null,
                  },
                },
              },
            },
            targets: [
              {
                target_id: 'new-parser',
                path: 'new_parser::parse',
                signature: 'parse(text, expected, sample) -> Result<String>',
                support: { status: 'supported' },
              },
            ],
            requirements: [
              {
                id: requirement,
                dimension: 'input_family',
                description: 'Text and binary public input with a latency budget',
                lanes: ['parity', 'coverage', 'benchmark'],
                target_profiles: ['native'],
                budget: {
                  kind: 'absolute',
                  metric: 'latency',
                  statistic: 'median',
                  operator: 'less_than_or_equal',
                  value: 10,
                  unit: 'millisecond',
                  baseline_subject: null,
                },
              },
            ],
            parity: {
              applicability: 'required',
              target_profiles: ['native'],
            },
            coverage: {
              applicability: 'required',
              target_profiles: ['native'],
              component_ids: ['parser-core'],
            },
            benchmark: {
              applicability: 'required',
              target_profiles: ['native'],
              metrics: ['latency'],
            },
          },
        ],
      },
    ],
    documentation: {
      command_id: 'docs',
      specification_outputs: ['docs/generated/public-contract.md'],
      evidence_outputs: ['docs/generated/status.md'],
    },
  };

  const parity = {
    schema: 'migration-parity/parity-input@1',
    cases: [
      {
        case_id: caseId,
        surface: 'Parser',
        operation: 'parse',
        covers: [requirement],
        target_profiles: ['native'],
        assets: [
          {
            id: 'sample',
            kind: 'ref',
            path: 'samples/input.bin',
            sha256: assetDigest,
            media_type: 'application/octet-stream',
          },
        ],
        steps: [
          {
            step_id: 'parse',
            surface: 'Parser',
            operation: 'parse',
            receiver: null,
            arguments: {
              text: { kind: 'literal', value: 'hello' },
              expected: { kind: 'literal', value: 'public input, not an oracle result' },
              sample: { kind: 'asset', asset_id: 'sample' },
            },
          },
        ],
        observations: ['parse'],
      },
    ],
  };

  const coverage = {
    schema: 'migration-parity/coverage-input@1',
    plans: [
      {
        plan_id: 'Parser.parse.public-paths',
        covers: [requirement],
        target_profile: 'native',
        selectors: {
          parity_case_ids: [caseId],
          command_ids: [],
        },
        component_ids: ['parser-core'],
        command_id: 'coverage',
      },
    ],
  };

  const benchmark = {
    schema: 'migration-parity/benchmark-input@1',
    workloads: [
      {
        workload_id: 'Parser.parse.standard-latency',
        covers: [requirement],
        subjects: [
          { kind: 'oracle', id: 'legacy' },
          { kind: 'target_profile', id: 'native' },
        ],
        input: { kind: 'parity_case', case_id: caseId },
        measurement: {
          boundary: 'observed_steps',
          step_ids: ['parse'],
          metrics: ['latency'],
          warmup_iterations: 2,
          measurement_iterations: 10,
          samples: 3,
          concurrency: 1,
          cache_state: 'warm',
          correctness_gate: 'parity_pass',
        },
      },
    ],
    suites: [
      {
        suite_id: 'Parser.parse.interactive',
        description: 'Interactive parse workload',
        members: [
          {
            workload_id: 'Parser.parse.standard-latency',
            weight: 1,
          },
        ],
      },
    ],
  };

  return {
    assetBytes,
    manifest,
    parity,
    coverage,
    benchmark,
  };
}

function validFiles(contract = validContract()) {
  return {
    'tests/fixtures/manifest.yaml': JSON.stringify(contract.manifest, null, 2),
    'tests/fixtures/assets/samples/input.bin': contract.assetBytes,
    'tests/fixtures/inputs/parity/parser.json': JSON.stringify(contract.parity, null, 2),
    'tests/fixtures/inputs/coverage/parser.json': JSON.stringify(contract.coverage, null, 2),
    'tests/fixtures/inputs/benchmark/parser.json': JSON.stringify(contract.benchmark, null, 2),
  };
}

test('audit accepts the fixed manifest and all three input interfaces', async (t) => {
  const root = await fixture(validFiles());
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.equal(report.schema, 'migration-parity/static-audit@2');
  assert.equal(report.summary.errors, 0);
  assert.equal(report.inventory.operations, 1);
  assert.equal(report.inventory.requirements, 1);
  assert.deepEqual(report.inventory.items, {
    parity_cases: 1,
    coverage_plans: 1,
    benchmark_workloads: 1,
    benchmark_suites: 1,
  });
  assert.deepEqual(report.specification_completeness.input_mapping, {
    parity: { numerator: 1, denominator: 1 },
    coverage: { numerator: 1, denominator: 1 },
    benchmark: { numerator: 1, denominator: 1 },
  });
  assert.deepEqual(report.specification_completeness.operation_contracts, {
    numerator: 1,
    denominator: 1,
  });
});

test('public input named expected and input asset digest are valid', async (t) => {
  const root = await fixture(validFiles());
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const codes = JSON.parse(result.stdout).findings.map((entry) => entry.code);

  assert.ok(!codes.includes('unknown_step_argument'));
  assert.ok(!codes.includes('asset_digest_mismatch'));
});

test('audit rejects unknown structural result fields and undeclared arguments', async (t) => {
  const contract = validContract();
  contract.parity.cases[0].expected = 'embedded result';
  contract.parity.cases[0].steps[0].arguments.undeclared = {
    kind: 'literal',
    value: true,
  };
  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((entry) => entry.code);

  assert.ok(codes.includes('unknown_schema_field'));
  assert.ok(codes.includes('unknown_step_argument'));
  assert.deepEqual(report.specification_completeness.input_mapping.parity, {
    numerator: 0,
    denominator: 1,
  });
});

test('target support claims agree with public path and signature fields', async (t) => {
  const missingPath = validContract();
  missingPath.manifest.surfaces[0].operations[0].targets[0].path = null;
  const missingPathRoot = await fixture(validFiles(missingPath));

  const unsupportedSignature = validContract();
  const target = unsupportedSignature.manifest.surfaces[0].operations[0].targets[0];
  target.support = {
    status: 'intentionally_unsupported',
    reason: 'The replacement intentionally omits this endpoint',
    authority: 'replacement public API policy',
  };
  const unsupportedSignatureRoot = await fixture(validFiles(unsupportedSignature));

  t.after(() => Promise.all([
    fs.rm(missingPathRoot, { recursive: true, force: true }),
    fs.rm(unsupportedSignatureRoot, { recursive: true, force: true }),
  ]));

  const missingPathResult = audit(missingPathRoot, '--strict');
  assert.equal(missingPathResult.status, 1, missingPathResult.stderr || missingPathResult.stdout);
  assert.ok(
    JSON.parse(missingPathResult.stdout).findings.some(
      (entry) => entry.code === 'implemented_target_without_path',
    ),
  );

  const unsupportedSignatureResult = audit(unsupportedSignatureRoot, '--strict');
  assert.equal(
    unsupportedSignatureResult.status,
    1,
    unsupportedSignatureResult.stderr || unsupportedSignatureResult.stdout,
  );
  assert.ok(
    JSON.parse(unsupportedSignatureResult.stdout).findings.some(
      (entry) => entry.code === 'nonendpoint_claim_has_signature',
    ),
  );
});

test('parameter omission is fixed and typed', async (t) => {
  const contract = validContract();
  contract.manifest.surfaces[0].operations[0].source.parameters[1].omission = {
    kind: 'literal',
    value: false,
  };
  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.ok(
    report.findings.some(
      (entry) => entry.code === 'parameter_default_type_mismatch',
    ),
  );
  assert.deepEqual(report.specification_completeness.operation_contracts, {
    numerator: 0,
    denominator: 1,
  });
});

test('comparison policies reject semantic escape hatches and implicit normalization', async (t) => {
  const contract = validContract();
  const resultContract = contract.manifest.surfaces[0].operations[0].source.result;
  resultContract.observations[0].comparison = { kind: 'semantic' };
  resultContract.error.message = {
    mode: 'normalized',
    transforms: [],
    reason: 'Unspecified normalization is not allowed',
  };

  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const codes = JSON.parse(result.stdout).findings.map((entry) => entry.code);

  assert.ok(codes.includes('invalid_observation_comparison'));
  assert.ok(codes.includes('normalized_message_without_transforms'));
});

test('multi-operation workflows only cover operations they observe', async (t) => {
  const contract = validContract();
  const operation = structuredClone(contract.manifest.surfaces[0].operations[0]);
  operation.id = 'tokenize';
  operation.source.path = 'legacy.Parser.tokenize';
  operation.source.signature = 'tokenize(text)';
  operation.targets[0].path = 'new_parser::tokenize';
  operation.targets[0].signature = 'tokenize(text) -> Result<Vec<String>>';
  operation.requirements = [
    {
      id: 'Parser.tokenize.text',
      dimension: 'input_family',
      description: 'Tokenize public text input',
      lanes: ['parity'],
      target_profiles: ['native'],
    },
  ];
  operation.parity = {
    applicability: 'required',
    target_profiles: ['native'],
  };
  operation.coverage = {
    applicability: 'not_applicable',
    reason: 'No separate coverage claim for this contract test',
  };
  operation.benchmark = {
    applicability: 'not_applicable',
    reason: 'No benchmark contract for this operation',
  };
  contract.manifest.surfaces[0].operations.push(operation);
  contract.parity.cases[0].covers.push('Parser.tokenize.text');

  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const result = audit(root, '--strict');

  assert.equal(result.status, 1, result.stderr || result.stdout);
  assert.ok(
    JSON.parse(result.stdout).findings.some(
      (entry) => entry.code === 'covered_operation_not_observed',
    ),
  );
});

test('coverage and benchmark selectors cannot claim unrelated workflows', async (t) => {
  const contract = validContract();
  const operation = structuredClone(contract.manifest.surfaces[0].operations[0]);
  operation.id = 'tokenize';
  operation.source.path = 'legacy.Parser.tokenize';
  operation.source.signature = 'tokenize(text)';
  operation.targets[0].path = 'new_parser::tokenize';
  operation.targets[0].signature = 'tokenize(text) -> Result<Vec<String>>';
  operation.requirements = [
    {
      id: 'Parser.tokenize.execution',
      dimension: 'code_path',
      description: 'Tokenize target execution path and latency',
      lanes: ['coverage', 'benchmark'],
      target_profiles: ['native'],
    },
  ];
  operation.parity = {
    applicability: 'not_applicable',
    reason: 'Covered by another public conformance system',
  };
  operation.coverage = {
    applicability: 'required',
    target_profiles: ['native'],
    component_ids: ['parser-core'],
  };
  operation.benchmark = {
    applicability: 'required',
    target_profiles: ['native'],
    metrics: ['latency'],
  };
  contract.manifest.surfaces[0].operations.push(operation);
  contract.coverage.plans[0].covers.push('Parser.tokenize.execution');
  contract.benchmark.workloads[0].covers.push('Parser.tokenize.execution');

  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const codes = JSON.parse(result.stdout).findings.map((entry) => entry.code);

  assert.ok(codes.includes('coverage_requirement_not_selected'));
  assert.ok(codes.includes('benchmark_requirement_not_in_case'));
  assert.ok(codes.includes('benchmark_operation_not_measured'));
});

test('audit rejects unsafe assets, duplicate item IDs, and unstable IDs', async (t) => {
  const contract = validContract();
  contract.parity.cases[0].case_id = 'Parser.parse.2026-07-31';
  contract.parity.cases[0].assets[0].path = '/tmp/source-output.bin';
  contract.coverage.plans[0].plan_id = 'Parser.parse.2026-07-31';
  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const codes = JSON.parse(result.stdout).findings.map((entry) => entry.code);

  assert.ok(codes.includes('nondeterministic_identifier'));
  assert.ok(codes.includes('duplicate_plan_id'));
  assert.ok(codes.includes('unsafe_relative_path'));
});

test('audit detects per-profile requirement mapping gaps', async (t) => {
  const contract = validContract();
  contract.manifest.target_profiles.push({
    id: 'wasm',
    target_id: 'new-parser',
    backend: 'wasm',
    features: ['default'],
  });
  const operation = contract.manifest.surfaces[0].operations[0];
  operation.requirements[0].target_profiles.push('wasm');
  operation.parity.target_profiles.push('wasm');
  operation.benchmark.target_profiles.push('wasm');
  contract.parity.cases[0].target_profiles.push('wasm');
  // Coverage remains intentionally native-only and its requirement still names wasm.
  operation.coverage.target_profiles.push('wasm');

  const root = await fixture(validFiles(contract));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const findings = JSON.parse(result.stdout).findings;

  assert.ok(
    findings.some(
      (entry) =>
        entry.code === 'unmapped_requirement'
        && entry.message.includes('coverage')
        && entry.message.includes('wasm'),
    ),
  );
  assert.ok(
    findings.some(
      (entry) =>
        entry.code === 'unmapped_requirement'
        && entry.message.includes('benchmark')
        && entry.message.includes('wasm'),
    ),
  );
});

test('audit supports an explicitly selected non-default manifest path', async (t) => {
  const files = validFiles();
  files['spec/manifest.yaml'] = files['tests/fixtures/manifest.yaml'];
  files['spec/assets/samples/input.bin'] = files['tests/fixtures/assets/samples/input.bin'];
  files['spec/inputs/parity/parser.json'] = files['tests/fixtures/inputs/parity/parser.json'];
  files['spec/inputs/coverage/parser.json'] = files['tests/fixtures/inputs/coverage/parser.json'];
  files['spec/inputs/benchmark/parser.json'] = files['tests/fixtures/inputs/benchmark/parser.json'];
  delete files['tests/fixtures/manifest.yaml'];
  delete files['tests/fixtures/assets/samples/input.bin'];
  delete files['tests/fixtures/inputs/parity/parser.json'];
  delete files['tests/fixtures/inputs/coverage/parser.json'];
  delete files['tests/fixtures/inputs/benchmark/parser.json'];
  const root = await fixture(files);
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict', '--manifest', 'spec/manifest.yaml');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(JSON.parse(result.stdout).manifest, 'spec/manifest.yaml');
});

test('audit requires the selected manifest and rejects duplicate active manifests', async (t) => {
  const missingRoot = await fixture({});
  const duplicateFiles = validFiles();
  duplicateFiles['tests/fixtures/nested/manifest.yaml'] = duplicateFiles['tests/fixtures/manifest.yaml'];
  const duplicateRoot = await fixture(duplicateFiles);
  t.after(() => Promise.all([
    fs.rm(missingRoot, { recursive: true, force: true }),
    fs.rm(duplicateRoot, { recursive: true, force: true }),
  ]));

  const missing = audit(missingRoot, '--strict');
  assert.equal(missing.status, 1, missing.stderr || missing.stdout);
  assert.ok(
    JSON.parse(missing.stdout).findings.some(
      (entry) => entry.code === 'missing_manifest',
    ),
  );

  const duplicate = audit(duplicateRoot, '--strict');
  assert.equal(duplicate.status, 1, duplicate.stderr || duplicate.stdout);
  assert.ok(
    JSON.parse(duplicate.stdout).findings.some(
      (entry) => entry.code === 'multiple_active_manifests',
    ),
  );
});

test('text output states the static audit limits', async (t) => {
  const root = await fixture(validFiles());
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = spawnSync('python3', ['-B', script, root], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /Migration parity specification audit/);
  assert.match(
    result.stdout,
    /does not prove live parity, coverage, benchmarks, result compatibility, or documentation freshness/i,
  );
});
