import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const script = path.resolve(
  'plugins/rust-development/skills/release-rust-crate/scripts/audit_release.py',
);

function run(command, args, cwd) {
  return spawnSync(command, args, { cwd, encoding: 'utf8' });
}

async function write(root, relativePath, contents) {
  const destination = path.join(root, relativePath);
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, contents);
}

async function fixture({ production }) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'release-rust-crate-'));
  const manifest = production
    ? [
        '[package]',
        'name = "release-fixture"',
        'version = "1.2.3"',
        'edition = "2021"',
        'rust-version = "1.74"',
        'description = "Release audit fixture"',
        'license = "MIT"',
        'repository = "https://example.com/release-fixture"',
        'homepage = "https://example.com/release-fixture"',
        'readme = "README.md"',
        'keywords = ["release"]',
        'categories = ["development-tools"]',
        'publish = ["crates-io"]',
        '',
      ].join('\n')
    : [
        '[package]',
        'name = "release-fixture"',
        'version = "1.2.3"',
        'edition = "2021"',
        '',
      ].join('\n');
  await write(root, 'Cargo.toml', manifest);
  await write(root, 'src/lib.rs', 'pub fn answer() -> u8 { 42 }\n');
  if (production) {
    await write(root, 'README.md', '# Release fixture\n');
    await write(root, 'CHANGELOG.md', '# Changelog\n\n## 1.2.3\n\n- Ready.\n');
    await write(
      root,
      '.github/workflows/release.yml',
      [
        'name: Release',
        'on:',
        '  push:',
        '    tags: ["v*"]',
        'permissions:',
        '  contents: read',
        'jobs:',
        '  publish:',
        '    runs-on: ubuntu-latest',
        '    timeout-minutes: 10',
        '    environment: crates-io',
        '    permissions:',
        '      contents: read',
        '      id-token: write',
        '    steps:',
        `      - uses: actions/checkout@${'a'.repeat(40)} # v4`,
        '      - name: Verify tag',
        '        run: test "${GITHUB_REF_NAME#v}" = "$(cargo metadata --no-deps --format-version 1 | jq -r .packages[0].version)"',
        '      - id: auth',
        `        uses: rust-lang/crates-io-auth-action@${'b'.repeat(40)} # v1`,
        '      - run: cargo publish --locked --registry crates-io',
        '        env:',
        '          CARGO_REGISTRY_TOKEN: ${{ steps.auth.outputs.token }}',
        '',
      ].join('\n'),
    );
  } else {
    await write(
      root,
      '.github/workflows/release.yml',
      [
        'name: Unsafe release',
        'on:',
        '  pull_request_target:',
        'jobs:',
        '  publish:',
        '    runs-on: ubuntu-latest',
        '    steps:',
        '      - uses: actions/checkout@v4',
        '      - run: cargo publish --allow-dirty',
        '        env:',
        '          CARGO_REGISTRY_TOKEN: ${{ secrets.CRATES_IO_TOKEN }}',
        '',
      ].join('\n'),
    );
  }

  const lock = run('cargo', ['generate-lockfile', '--manifest-path', 'Cargo.toml'], root);
  assert.equal(lock.status, 0, lock.stderr || lock.stdout);
  assert.equal(run('git', ['init', '-q'], root).status, 0);
  assert.equal(run('git', ['add', '.'], root).status, 0);
  const commit = run(
    'git',
    [
      '-c',
      'user.name=Release Tests',
      '-c',
      'user.email=release@example.com',
      'commit',
      '-qm',
      'fixture',
    ],
    root,
  );
  assert.equal(commit.status, 0, commit.stderr || commit.stdout);
  if (!production) {
    await write(root, 'dirty.txt', 'uncommitted\n');
  }
  return root;
}

function audit(root, ...args) {
  return run('python3', [script, root, '--format', 'json', ...args], root);
}

test('audit accepts a clean pinned OIDC release structure', async (t) => {
  const root = await fixture({ production: true });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--expected-version', '1.2.3', '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.equal(report.schema_version, 1);
  assert.equal(report.inventory.git.dirty_entries, 0);
  assert.equal(report.inventory.packages[0].name, 'release-fixture');
  assert.equal(report.inventory.packages[0].version, '1.2.3');
  assert.deepEqual(report.inventory.workflows.release_workflows, [
    '.github/workflows/release.yml',
  ]);
  assert.equal(report.summary.errors, 0);
});

test('strict audit rejects dirty, unpinned, secret-backed publication', async (t) => {
  const root = await fixture({ production: false });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--expected-version', '1.2.4', '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = new Set(report.findings.map((finding) => finding.code));

  for (const code of [
    'dirty_worktree',
    'missing_description',
    'missing_license',
    'version_mismatch',
    'unpinned_action',
    'privileged_pull_request_target',
    'release_permissions_not_minimal',
    'publish_not_locked',
    'publish_allows_dirty',
    'long_lived_registry_secret',
  ]) {
    assert.ok(codes.has(code), `missing finding: ${code}`);
  }
});

test('text audit states its evidence limits', async (t) => {
  const root = await fixture({ production: true });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = run('python3', [script, root], root);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /Rust release static evidence inventory/);
  assert.match(result.stdout, /does not prove API compatibility, test correctness/);
  assert.match(result.stdout, /inspect the \.crate/i);
  assert.match(result.stdout, /exact registry artifact from a clean consumer environment/);
});

test('audit rejects a missing manifest without a traceback', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'release-rust-crate-empty-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = run('python3', [script, root], root);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /Cargo manifest does not exist/);
  assert.doesNotMatch(result.stderr, /Traceback/);
});
