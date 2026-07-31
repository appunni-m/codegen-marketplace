import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
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
  return spawnSync('python3', [script, root, '--format', 'json', ...args], {
    encoding: 'utf8',
  });
}

test('audit accepts deterministic input-only parity fixtures', async (t) => {
  const root = await fixture({
    'tests/fixtures/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/assets/samples/input.bin': 'fixture bytes',
    'tests/fixtures/inputs/Parser/parse.json': JSON.stringify({
      version: 1,
      surface: 'Parser',
      operation: 'parse',
      cases: [
        {
          case_id: 'Parser.parse.empty_input',
          operation: 'parse',
          inputs: { assets: {}, params: { text: '' } },
        },
        {
          case_id: 'Parser.parse.binary_fixture',
          operation: 'parse',
          inputs: {
            assets: {
              sample: { kind: 'ref', path: 'samples/input.bin' },
            },
            params: {},
          },
        },
      ],
    }),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.equal(report.schema_version, 1);
  assert.equal(report.summary.errors, 0);
  assert.equal(report.inventory.case_count, 2);
  assert.deepEqual(report.inventory.case_ids, [
    'Parser.parse.binary_fixture',
    'Parser.parse.empty_input',
  ]);
  assert.deepEqual(report.inventory.input_files, [
    'tests/fixtures/inputs/Parser/parse.json',
  ]);
});

test('audit rejects embedded expectations, duplicate IDs, and unsafe assets', async (t) => {
  const root = await fixture({
    'tests/fixtures/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/inputs/Parser/parse.json': JSON.stringify({
      version: 1,
      surface: 'Parser',
      operation: 'parse',
      cases: [
        {
          case_id: 'Parser.parse.2026-07-31',
          operation: 'parse',
          inputs: {
            assets: {
              sample: { kind: 'ref', path: '/tmp/source-output.bin' },
            },
            params: { expected: 'accepted' },
          },
        },
        {
          case_id: 'Parser.parse.2026-07-31',
          operation: 'decode',
          inputs: { assets: {}, params: {} },
        },
      ],
    }),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((finding) => finding.code);

  assert.ok(codes.includes('forbidden_expected_key'));
  assert.ok(codes.includes('duplicate_case_id'));
  assert.ok(codes.includes('case_operation_mismatch'));
  assert.ok(codes.includes('unsafe_asset_path'));
  assert.ok(codes.includes('nondeterministic_case_id'));
});

test('audit requires exactly one active manifest at the canonical path', async (t) => {
  const missingRoot = await fixture({
    'tests/fixtures/inputs/Parser/parse.json': '{"version":1,"surface":"Parser","operation":"parse","cases":[]}',
  });
  const duplicateRoot = await fixture({
    'tests/fixtures/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/nested/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/inputs/Parser/parse.json': '{"version":1,"surface":"Parser","operation":"parse","cases":[]}',
  });
  t.after(() => Promise.all([
    fs.rm(missingRoot, { recursive: true, force: true }),
    fs.rm(duplicateRoot, { recursive: true, force: true }),
  ]));

  const missing = audit(missingRoot, '--strict');
  assert.equal(missing.status, 1, missing.stderr || missing.stdout);
  assert.ok(
    JSON.parse(missing.stdout).findings.some(
      (finding) => finding.code === 'missing_manifest',
    ),
  );

  const duplicate = audit(duplicateRoot, '--strict');
  assert.equal(duplicate.status, 1, duplicate.stderr || duplicate.stdout);
  assert.ok(
    JSON.parse(duplicate.stdout).findings.some(
      (finding) => finding.code === 'multiple_active_manifests',
    ),
  );
});

test('audit rejects malformed document and case shapes', async (t) => {
  const root = await fixture({
    'tests/fixtures/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/inputs/bad.json': JSON.stringify({
      version: 2,
      surface: 'Parser',
      operation: 'parse',
      cases: [
        {
          case_id: 'Parser.parse.extra_key',
          operation: 'parse',
          inputs: { assets: {}, params: {}, extra: true },
          expected: 'no',
        },
      ],
      outputs: [],
    }),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((finding) => finding.code);

  assert.ok(codes.includes('unsupported_document_version'));
  assert.ok(codes.includes('invalid_document_keys'));
  assert.ok(codes.includes('invalid_case_keys'));
  assert.ok(codes.includes('invalid_inputs_keys'));
});

test('text output states static validation limits', async (t) => {
  const root = await fixture({
    'tests/fixtures/manifest.yaml': 'version: 1\nsurfaces: []\n',
    'tests/fixtures/inputs/Parser/parse.json': '{"version":1,"surface":"Parser","operation":"parse","cases":[]}',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = spawnSync('python3', [script, root], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Migration parity fixture audit/);
  assert.match(result.stdout, /does not prove live parity or coverage/i);
});
