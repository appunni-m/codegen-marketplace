import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const coverageSource = 'git+https://github.com/appunni-m/coverage-mcp.git@main';

async function read(pathname) {
  return fs.readFile(pathname, 'utf8');
}

test('release metadata uses stable plugin versions and tracks Coverage MCP main', async () => {
  for (const manifestPath of [
    'plugins/testing/.claude-plugin/plugin.json',
    'plugins/testing/.codex-plugin/plugin.json',
  ]) {
    const manifest = JSON.parse(await read(manifestPath));
    assert.equal(manifest.version, '0.3.0', manifestPath);
    assert.equal(manifest.mcpServers['coverage-mcp'].args[1], coverageSource, manifestPath);
    assert.doesNotMatch(manifest.version, /\+codex\./, manifestPath);
  }

  for (const pathname of [
    'README.md',
    'plugins/testing/README.md',
    'plugins/testing/compatibility.json',
    'plugins/testing/scripts/install-pi-mcp.mjs',
  ]) {
    const contents = await read(pathname);
    assert.ok(contents.includes(coverageSource), pathname);
    assert.doesNotMatch(contents, /coverage-mcp\.git@v\d/, pathname);
  }
});

test('runtime DuckDB state is ignored', async () => {
  const gitignore = await read('.gitignore');
  assert.match(gitignore, /^\.coverage-mcp\/$/m);
  assert.match(gitignore, /^\*\.duckdb$/m);
  assert.match(gitignore, /^\*\.duckdb\.wal$/m);
});

test('Coverage MCP reports include the local dashboard handoff', async () => {
  const skill = await read('plugins/testing/skills/use-coverage-mcp/SKILL.md');
  assert.match(skill, /http:\/\/localhost:59471\//);
  assert.match(skill, /After the managed task reaches a terminal state/);
  assert.match(skill, /Do not open the browser automatically/);
});

test('third-party notices preserve upstream copyright statements', async () => {
  const repositoryNotice = await read('THIRD_PARTY_NOTICES.md');
  const pluginNotice = await read('plugins/rust-development/THIRD_PARTY_NOTICES.md');
  const skillNotice = await read(
    'plugins/rust-development/skills/rust-development/references/THIRD_PARTY_NOTICES.md',
  );

  assert.match(repositoryNotice, /Copyright \(c\) 2026 Mike North/);
  assert.match(repositoryNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
  assert.match(pluginNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
  assert.match(skillNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
});
