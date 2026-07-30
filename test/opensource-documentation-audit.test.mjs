import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const script = path.resolve(
  'plugins/opensource/skills/opensource-documentation/scripts/audit_documentation.py',
);

async function fixture(files) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'opensource-docs-'));
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

test('documentation audit inventories project evidence deterministically', async (t) => {
  const root = await fixture({
    'README.md': [
      '# Sample',
      '',
      'A small example project.',
      '',
      '## Installation',
      '',
      '```bash',
      'python -m sample',
      '```',
      '',
      '## Usage',
      '',
      'Read the [guide](docs/guide.md#run).',
      '',
      '## Contributing',
      '',
      'See CONTRIBUTING.md.',
      '',
      '## Security',
      '',
      'See SECURITY.md.',
      '',
      '## License',
      '',
      'MIT.',
    ].join('\n'),
    'LICENSE': 'MIT License\n',
    'CONTRIBUTING.md': '# Contributing\n\n```\npnpm test\n```\n',
    'SECURITY.md': '# Security\n',
    'docs/guide.md': '# Guide\n\n## Run\n',
    'pyproject.toml': '[project]\nname = "sample"\n',
    'src/sample.py': 'def main():\n    return 0\n',
    'node_modules/ignored.ts': 'export const ignored = true;\n',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.equal(report.schema_version, 1);
  assert.deepEqual(report.summary, { errors: 0, info: 0, review: 1 });
  assert.deepEqual(report.inventory.languages, [
    { files: 1, language: 'Python' },
  ]);
  assert.ok(
    report.inventory.project_markers.some(
      (item) => item.path === 'pyproject.toml' && item.kind === 'Python',
    ),
  );
  assert.deepEqual(report.inventory.root_documents.readme, ['README.md']);
  assert.deepEqual(report.inventory.root_documents.license, ['LICENSE']);
  assert.deepEqual(report.inventory.readme_topics_observed, [
    'installation_or_quick_start',
    'usage',
    'contributing',
    'security',
    'license',
  ]);
  assert.equal(report.findings[0].code, 'unlabeled_code_fence');
  assert.equal(report.findings[0].path, 'CONTRIBUTING.md');
});

test('strict audit fails for broken local links and unbalanced fences', async (t) => {
  const root = await fixture({
    'README.md': [
      '# Broken',
      '',
      '[Missing guide](docs/missing.md)',
      '',
      '```sh',
      'echo broken',
    ].join('\n'),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((finding) => finding.code);

  assert.ok(codes.includes('broken_local_link'));
  assert.ok(codes.includes('unbalanced_code_fence'));
  assert.equal(report.summary.errors, 2);
});

test('audit rejects a path that is not a directory', () => {
  const result = spawnSync(
    'python3',
    [script, path.join(os.tmpdir(), 'opensource-docs-path-does-not-exist')],
    { encoding: 'utf8' },
  );

  assert.equal(result.status, 2);
  assert.match(result.stderr, /repository is not a directory/);
});

test('text output states the semantic limits of the audit', async (t) => {
  const root = await fixture({
    'README.md': '# Sample\n',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = spawnSync('python3', [script, root], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Documentation evidence inventory/);
  assert.match(result.stdout, /do not prove that documentation is accurate or useful/);
  assert.match(result.stdout, /External URL availability/);
});
