import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/opensource/skills/build-migration-parity-tests';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

function compact(value) {
  return value.replace(/\s+/g, ' ');
}

test('migration parity builder stays compact and broadly triggered', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 220, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1500, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: build-migration-parity-tests$/m);
  assert.match(skill, /^description: Build.+migration.+parity.+$/m);
  assert.match(skill, /API, CLI, ABI, protocol, service, file format, or library/i);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
});

test('skill requires executable parity, coverage, benchmark, aggregation, and docs lanes', async () => {
  const skill = compact(await read('SKILL.md'));

  assert.match(skill, /Create or update executable repository files/i);
  assert.match(skill, /Do not stop at an audit, design, or name inventory/i);
  assert.match(skill, /live oracle.*public targets.*comparator.*parity result/is);
  assert.match(skill, /managed instrumented execution.*coverage result/is);
  assert.match(skill, /correctness-gated measurements.*benchmark result/is);
  assert.match(skill, /aggregate status.*generated documentation/is);
  assert.match(skill, /repository-native parity, coverage, benchmark, aggregation, docs/is);
});

test('manifest is a fixed specification rather than a result or extension registry', async () => {
  const skill = compact(await read('SKILL.md'));
  const manifest = compact(await read('references/manifest-contract.md'));

  assert.match(skill, /fixed versioned interfaces and reject unknown fields/i);
  assert.match(skill, /not a dynamic schema/i);
  assert.match(skill, /reviewed schema version.*deterministic migration/is);
  assert.match(manifest, /Do not add a numeric `version`/i);
  for (const observedState of ['current revisions', 'pass/fail', 'timings', 'run IDs']) {
    assert.match(manifest, new RegExp(observedState, 'i'));
  }
  assert.match(manifest, /Do not store `active`,\s*`pending`, `blocked`/i);
  assert.match(manifest, /extension maps.*catch-all metadata/i);
});

test('contract supports canonical nested identities and several target profiles', async () => {
  const manifest = compact(await read('references/manifest-contract.md'));
  const standard = compact(await read('references/standard.md'));

  assert.match(manifest, /`PIL\.ImageFont`, not `font`/);
  assert.match(manifest, /Surface IDs may contain dots/i);
  assert.match(manifest, /Several oracles are allowed/i);
  assert.match(manifest, /target profile.*runtime\/backend\/feature/is);
  assert.match(standard, /C ABI and compile-time surface/i);
  assert.match(standard, /Image and file-format surface/i);
  assert.match(standard, /detect, inspect, verify, decode.*encode/is);
});

test('parity input is a typed public workflow and allows legitimate public field names', async () => {
  const manifest = compact(
    `${await read('references/manifest-contract.md')} ${await read('references/standard.md')}`,
  );

  assert.match(manifest, /typed parameter table/i);
  assert.match(manifest, /assets \+ ordered public steps \+ bindings \+ observed steps/i);
  assert.match(manifest, /constructor.*methods, ABI handle lifetimes/is);
  assert.match(manifest, /Value descriptors are exact discriminated objects/i);
  assert.match(manifest, /legitimate public parameters\s+named `status`, `output`, `expected`, or `error`/i);
  assert.match(manifest, /Input digests are allowed and encouraged/i);
  assert.match(manifest, /Expected output digests remain forbidden/i);
});

test('coverage and benchmarks use distinct strict interfaces', async () => {
  const manifest = compact(await read('references/manifest-contract.md'));
  const evidence = compact(await read('references/evidence-contract.md'));

  assert.match(manifest, /Code coverage is many-to-many/i);
  assert.match(manifest, /unverifiable free-form repository-test ID registry/i);
  assert.match(manifest, /measurement boundaries are `observed_steps`, `whole_workflow`, `process`, and `artifact`/i);
  assert.match(manifest, /weighted real-world profiles/i);
  assert.match(evidence, /integer covered and total counts/i);
  assert.match(evidence, /budget.*`not_proven`.*correctness gate/is);
  assert.match(evidence, /Never compare benchmark baselines across incompatible/is);
});

test('result and aggregate interfaces preserve multi-profile evidence identity', async () => {
  const evidence = compact(await read('references/evidence-contract.md'));

  for (const schema of [
    'migration-parity/parity-result@1',
    'migration-parity/coverage-result@1',
    'migration-parity/benchmark-result@1',
    'migration-parity/status-report@1',
  ]) {
    assert.match(evidence, new RegExp(schema.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }

  assert.match(evidence, /one comparison for every selected case\/target-profile pair/i);
  assert.match(evidence, /manifest path, schema, and digest match/i);
  assert.match(evidence, /missing, stale, cancelled, invalid.*`not_proven`/is);
  assert.match(evidence, /specification reference.*current evidence status/is);
});

test('deprecation and anti-cheat rules do not confuse fixtures with public support', async () => {
  const skill = compact(await read('SKILL.md'));
  const standard = compact(await read('references/standard.md'));

  assert.match(skill, /Never mark `support\.status: deprecated` merely because old fixtures moved/i);
  assert.match(skill, /Do not delete first/i);
  assert.match(skill, /case-specific comparison/i);
  assert.match(skill, /circular oracles/i);
  assert.match(standard, /Fixture deprecation is not public API deprecation/i);
  assert.match(standard, /coverage exclusions manufacture completeness/i);
  assert.match(standard, /budget pass ignores correctness/i);
});

test('evals probe strict interface and evidence failures', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'build-migration-parity-tests');
  assert.ok(payload.evals.length >= 9);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');

  for (const scenario of [
    'Python',
    'Rust',
    'CLI',
    'HTTP',
    'C ABI',
    'codec',
    'benchmark',
    'coverage',
    'unknown field',
  ]) {
    assert.match(prompts, new RegExp(scenario, 'i'), `missing eval scenario: ${scenario}`);
  }

  for (const behavior of [
    'live source',
    'input-only',
    'target profile',
    'not_proven',
    'public surface',
    'does not delete',
    'correctness-gated',
    'fixed schema',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing eval behavior: ${behavior}`);
  }
});

test('skill UI metadata invokes the complete evidence-system workflow', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Build Migration Parity Tests"/);
  assert.match(metadata, /short_description: "Build strict migration evidence systems"/);
  assert.match(metadata, /default_prompt: "Use \$build-migration-parity-tests /);
  assert.match(metadata, /parity, coverage, benchmark, and generated status documentation/i);
});
