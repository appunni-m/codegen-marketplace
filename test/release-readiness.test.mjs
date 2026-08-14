import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

async function read(pathname) {
  return fs.readFile(pathname, 'utf8');
}

test('release metadata uses stable versions and the pinned Coverage MCP bootstrap', async () => {
  const expectedVersions = new Map([
    ['plugins/testing/.claude-plugin/plugin.json', '0.5.0'],
    ['plugins/testing/.codex-plugin/plugin.json', '0.5.0'],
    ['plugins/rust-development/gemini-extension.json', '0.3.1'],
  ]);

  for (const [manifestPath, expectedVersion] of expectedVersions) {
    const manifest = JSON.parse(await read(manifestPath));
    assert.equal(manifest.version, expectedVersion, manifestPath);
    if (manifestPath.includes('.codex-plugin')) {
      assert.equal(manifest.mcpServers, './.mcp.json', manifestPath);
    } else {
      assert.deepEqual(
        manifest.mcpServers['coverage-mcp'],
        { command: 'coverage-mcp', args: ['connect'] },
        manifestPath,
      );
    }
    assert.doesNotMatch(manifest.version, /\+codex\./, manifestPath);
  }

  const bundledMcp = JSON.parse(await read('plugins/testing/.mcp.json'));
  assert.deepEqual(
    bundledMcp.mcpServers['coverage-mcp'],
    {
      command: './bin/coverage-mcp-launcher',
      args: [],
      startup_timeout_sec: 900,
    },
  );
  const compatibility = JSON.parse(await read('plugins/testing/compatibility.json'));
  assert.equal(compatibility.coverageMcp.schemaRevision, 7);
  assert.equal(compatibility.coverageMcp.toolCount, 11);
  assert.equal(compatibility.coverageMcp.sharedDaemon.defaultPort, 59471);
  assert.equal(compatibility.coverageMcp.sharedDaemon.connectionLock, false);
  assert.equal(
    compatibility.coverageMcp.sharedDaemon.ownershipLockFile,
    '<common-db-parent>/daemon.lock',
  );
  assert.equal(
    compatibility.coverageMcp.sharedDaemon.projectDatabase,
    '<canonical-git-root>/.coverage-mcp/coverage.duckdb',
  );
  assert.deepEqual(compatibility.coverageMcp.nativeConnector, {
    command: 'coverage-mcp',
    args: ['connect'],
  });
  assert.equal(compatibility.coverageMcp.bootstrap.manager, 'cargo');
  assert.equal(compatibility.coverageMcp.bootstrap.package, 'coverage-mcp');
  assert.equal(compatibility.coverageMcp.bootstrap.version, '=0.8.3');
  assert.deepEqual(compatibility.coverageMcp.bootstrap.platforms, [
    'macos',
    'linux',
    'wsl',
  ]);
  assert.equal(compatibility.coverageMcp.bootstrap.nativeWindows, false);

  const launcher = await read('plugins/testing/bin/coverage-mcp-launcher');
  assert.match(launcher, /version="0\.8\.3"/);
  assert.match(launcher, /cargo_binary.*install/);
  assert.match(launcher, /\.install-\$\{version\}\.lock/);
  if (process.platform !== 'win32') {
    const mode = (await fs.stat('plugins/testing/bin/coverage-mcp-launcher')).mode & 0o777;
    assert.equal(mode, 0o755);
  }

  for (const pathname of [
    'README.md',
    'plugins/testing/README.md',
    'plugins/testing/compatibility.json',
    'plugins/testing/bin/coverage-mcp-launcher',
    'plugins/testing/scripts/install-pi-mcp.mjs',
  ]) {
    const contents = await read(pathname);
    assert.match(contents, /coverage-mcp/, pathname);
    assert.doesNotMatch(contents, /uvx --from|python -m pip install/, pathname);
  }

  for (const pathname of ['README.md', 'plugins/testing/README.md']) {
    assert.match(await read(pathname), /cargo run --locked/, pathname);
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
  assert.match(skill, /reaches a\s+terminal state/);
  assert.match(skill, /Do not open the browser automatically/);
});

test('third-party notices preserve upstream copyright statements', async () => {
  const repositoryNotice = await read('THIRD_PARTY_NOTICES.md');
  const pluginNotice = await read('plugins/rust-development/THIRD_PARTY_NOTICES.md');
  const skillNotice = await read(
    'plugins/rust-development/skills/rust-development/references/THIRD_PARTY_NOTICES.md',
  );
  const codingGuidelinesNotice = await read(
    'plugins/rust-development/skills/coding-guidelines/references/THIRD_PARTY_NOTICES.md',
  );

  assert.match(repositoryNotice, /Copyright \(c\) 2026 Mike North/);
  assert.match(repositoryNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
  assert.match(repositoryNotice, /Copyright \(c\) 2025 Leonardo Maldonado/);
  assert.match(pluginNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
  assert.match(pluginNotice, /Copyright \(c\) 2025 Leonardo Maldonado/);
  assert.match(skillNotice, /Copyright \(c\) 2024 Apollo Graph, Inc\./);
  assert.match(codingGuidelinesNotice, /Copyright \(c\) 2025 Leonardo Maldonado/);
});

test('distributed plugins preserve the repository MIT copyright notice', async () => {
  for (const pathname of [
    'LICENSE',
    'plugins/testing/LICENSE',
  ]) {
    const license = await read(pathname);
    assert.match(license, /^MIT License$/m, pathname);
    assert.match(license, /^Copyright \(c\) 2026 Appunni M$/m, pathname);
  }
});
