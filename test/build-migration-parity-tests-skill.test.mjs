import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/opensource/skills/build-migration-parity-tests';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

test('migration parity test builder stays compact and language agnostic', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 220, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1500, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: build-migration-parity-tests$/m);
  assert.match(skill, /^description: [Bb]uild.+migration.+parity.+$/m);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
  assert.match(skill, /language-agnostic/i);
  assert.match(skill, /API, CLI, ABI, protocol, file format, service, or library/i);
  assert.match(skill, /public-behavior parity/i);
  assert.match(skill, /not a general implementation rewrite/i);
});

test('skill builds a runnable harness rather than stopping at verification advice', async () => {
  const skill = await read('SKILL.md');

  assert.match(skill, /create or update actual repository files/i);
  assert.match(skill, /Do not stop at a report, plan, checklist, or audit/i);
  assert.match(skill, /Completion requires runnable checked-in test code/i);
  assert.match(skill, /one public surface/i);
  assert.match(skill, /manifest.*input fixtures.*source oracle.*target runner.*comparator/is);
  assert.match(skill, /repository-native test target/i);
  assert.match(skill, /run the harness/i);
  assert.match(skill, /verification is the final stage/i);
});

test('builder enforces the live differential parity pipeline', async () => {
  const skill = await read('SKILL.md');

  assert.match(
    skill,
    /input-only fixture.*live source oracle.*live target implementation.*normalized Result.*evidence ledger/is,
  );
  assert.match(skill, /source implementation is the oracle/i);
  assert.match(skill, /target implementation is the system under test/i);
  assert.match(skill, /oracle startup.*test failure/is);
  assert.match(skill, /result count.*input case count/is);
  assert.match(skill, /source ok.*target error.*fail/is);
  assert.match(skill, /source error.*target ok.*fail/is);
  assert.match(skill, /case-id-specific/i);
});

test('reference preserves manifest, fixture, result, and status contracts', async () => {
  const reference = await read('references/standard.md');

  for (const contract of [
    'tests/fixtures/manifest.yaml',
    'input_only',
    'live_oracle',
    'result_comparison',
    'active',
    'pending',
    'unsupported',
    'deprecated',
    'case_id',
    'assets',
    'params',
    'environment',
    'Result envelope',
    'status',
    'value',
    'error',
    'output shape',
    'public surface',
  ]) {
    assert.match(reference, new RegExp(contract, 'i'), `missing contract: ${contract}`);
  }

  for (const forbidden of [
    'expected',
    'golden',
    'oracle',
    'output',
    'pixels',
    'sha256',
    'status',
  ]) {
    assert.match(reference, new RegExp(`\\b${forbidden}\\b`, 'i'));
  }

  assert.match(reference, /Pending is not passing/i);
  assert.match(reference, /Do not delete first.*Migrate, prove, then delete/is);
  assert.match(reference, /pillow-rs project profile/i);
});

test('skill keeps parity, coverage, and reproducibility claims distinct', async () => {
  const skill = await read('SKILL.md');
  const reference = await read('references/standard.md');

  assert.match(skill, /Passing parity does not prove coverage/i);
  assert.match(skill, /Coverage does not prove parity/i);
  assert.match(skill, /fresh.*ingested coverage artifact/is);
  assert.match(skill, /not proven/i);
  assert.match(reference, /manifest path and hash/i);
  assert.match(reference, /input file list and hash/i);
  assert.match(reference, /asset file list and hash/i);
  assert.match(reference, /run id/i);
  assert.match(reference, /coverage snapshot id/i);
  assert.match(reference, /dirty\/clean status/i);
});

test('anti-cheat rules reject circular and hidden parity mechanisms', async () => {
  const skill = await read('SKILL.md');
  const reference = await read('references/standard.md');

  assert.match(skill, /target output.*oracle output/is);
  assert.match(skill, /target.*launch.*source oracle/is);
  assert.match(skill, /wrapper.*algorithms/is);
  assert.match(skill, /test-only parity branches/i);
  assert.match(reference, /active runner reads deprecated fixture roots/i);
  assert.match(reference, /coverage exclusions/i);
  assert.match(reference, /embedded expected output/i);
  assert.match(reference, /unclassified source\/target public names/i);
});

test('evals probe failures that superficial differential test builders miss', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'build-migration-parity-tests');
  assert.ok(payload.evals.length >= 7);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');

  for (const scenario of [
    'Python',
    'Rust',
    'CLI',
    'HTTP',
    'nondeterministic',
    'pending',
    'coverage',
    'wrapper',
  ]) {
    assert.match(prompts, new RegExp(scenario, 'i'), `missing eval scenario: ${scenario}`);
  }

  for (const behavior of [
    'creates',
    'live source',
    'input-only',
    'Result envelope',
    'not proven',
    'public surface',
    'does not delete',
    'anti-cheat',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing eval behavior: ${behavior}`);
  }
});

test('skill UI metadata explicitly invokes the skill', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Build Migration Parity Tests"/);
  assert.match(metadata, /short_description: "Build live-oracle migration parity suites"/);
  assert.match(metadata, /default_prompt: "Use \$build-migration-parity-tests /);
});
