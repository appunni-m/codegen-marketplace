import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/rust-development/skills/release-rust-crate';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

test('Rust release skill stays compact and routes production release work', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 260, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1900, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: release-rust-crate$/m);
  assert.match(skill, /^description: .+crates\.io.+GitHub.+SemVer.+MSRV.+Trusted Publishing.+Cargo workspace.+yank.+checklist\.$/m);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
  assert.match(skill, /Separate \*\*prepare\/audit\*\* authority from \*\*publish\/tag\/release\*\* authority/);
  assert.match(skill, /Never publish from a dirty worktree/);
  assert.match(skill, /Pin third-party GitHub Actions to reviewed full commit SHAs/);
  assert.match(skill, /audit_release\.py/);
  assert.match(skill, /prepared.*CI-proven.*published.*registry-visible.*consumer-verified.*released/s);
});

test('release references cover package, CI, first publish, workspace, and recovery boundaries', async () => {
  const readiness = await read('references/crate-readiness.md');
  const github = await read('references/github-ci-and-publishing.md');
  const recovery = await read('references/workspaces-and-recovery.md');

  for (const expected of [
    'Manifest and registry metadata',
    'Version and compatibility policy',
    'MSRV, targets, features, and dependencies',
    'Package archive inspection',
    'Clean-consumer verification',
  ]) {
    assert.ok(readiness.includes(expected), `missing readiness section: ${expected}`);
  }
  for (const expected of [
    'Trust boundaries',
    'Tag and version authority',
    'Trusted Publishing and first-release boundary',
    'Actions supply-chain hardening',
    'Reliability and autorecovery',
  ]) {
    assert.ok(github.includes(expected), `missing GitHub section: ${expected}`);
  }
  for (const expected of [
    'Workspace release graph',
    'First crates.io publication',
    'Registry propagation and idempotency',
    'Native binary releases',
    'Failure and recovery matrix',
  ]) {
    assert.ok(recovery.includes(expected), `missing recovery section: ${expected}`);
  }

  const all = `${readiness}\n${github}\n${recovery}`;
  assert.match(all, /cargo package --list/);
  assert.match(all, /cargo publish --locked/);
  assert.match(all, /id-token: write/);
  assert.match(all, /CARGO_REGISTRY_TOKEN/);
  assert.match(all, /full commit SHA/);
  assert.match(all, /cannot be overwritten/);
  assert.match(all, /cargo info/);
  assert.match(all, /cargo yank/);
});

test('release guidance uses current primary Rust and GitHub sources', async () => {
  const all = [
    await read('references/crate-readiness.md'),
    await read('references/github-ci-and-publishing.md'),
    await read('references/workspaces-and-recovery.md'),
  ].join('\n');

  for (const authority of [
    'https://doc.rust-lang.org/cargo/',
    'https://doc.rust-lang.org/rustdoc/',
    'https://rust-lang.github.io/rfcs/3691-trusted-publishing-cratesio.html',
    'https://github.com/rust-lang/crates-io-auth-action',
    'https://docs.github.com/',
  ]) {
    assert.ok(all.includes(authority), `missing primary authority: ${authority}`);
  }
});

test('skill evals cover materially different release and failure modes', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'release-rust-crate');
  assert.ok(payload.evals.length >= 8);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');
  for (const scenario of [
    'first crates.io release',
    'five-crate Cargo workspace',
    '--allow-dirty',
    'pull_request_target',
    'timed out',
    'prebuilt Linux, macOS, and Windows binaries',
    'do not commit, tag, publish',
    'docs.rs build failed',
  ]) {
    assert.ok(prompts.includes(scenario), `missing eval scenario: ${scenario}`);
  }
  for (const behavior of [
    'Trusted Publishing',
    'dependency graph',
    'full SHA',
    'registry propagation',
    'checksums',
    'read-only',
    'immutable',
    'new version',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing eval behavior: ${behavior}`);
  }
});

test('skill UI metadata explicitly invokes the release skill', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Release Rust Crate"/);
  assert.match(metadata, /short_description: "Audit and ship production-ready Rust crates"/);
  assert.match(metadata, /default_prompt: "Use \$release-rust-crate /);
});
