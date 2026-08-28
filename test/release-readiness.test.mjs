import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

async function read(pathname) {
  return fs.readFile(pathname, 'utf8');
}

test('release metadata uses stable versions and the pinned Coverage MCP bootstrap', async () => {
  const expectedVersions = new Map([
    ['plugins/testing/.claude-plugin/plugin.json', '0.7.3'],
    ['plugins/testing/.codex-plugin/plugin.json', '0.7.3'],
    ['plugins/rust-development/gemini-extension.json', '0.3.2'],
  ]);

  for (const [manifestPath, expectedVersion] of expectedVersions) {
    const manifest = JSON.parse(await read(manifestPath));
    if (manifestPath.includes('.codex-plugin')) {
      assert.match(
        manifest.version,
        new RegExp(`^${expectedVersion.replaceAll('.', '\\.')}(\\+codex\\..+)?$`),
        manifestPath,
      );
    } else {
      assert.equal(manifest.version, expectedVersion, manifestPath);
    }
    if (manifestPath.includes('.codex-plugin')) {
      assert.equal(manifest.mcpServers, './.mcp.json', manifestPath);
    } else {
      assert.deepEqual(
        manifest.mcpServers['coverage-mcp'],
        { command: 'coverage-mcp', args: ['connect'] },
        manifestPath,
      );
    }
    if (!manifestPath.includes('.codex-plugin')) {
      assert.doesNotMatch(manifest.version, /\+codex\./, manifestPath);
    }
  }

  const bundledMcp = JSON.parse(await read('plugins/testing/.mcp.json'));
  const connector = bundledMcp.mcpServers['coverage-mcp'];
  assert.equal(connector.command, '/bin/sh');
  assert.deepEqual(connector.args.slice(0, 2), ['-eu', '-c']);
  assert.equal(connector.args.length, 3);
  assert.equal(connector.cwd, undefined);
  assert.deepEqual(connector.env, { COVERAGE_MCP_VERSION: '0.15.3' });
  assert.equal(connector.startup_timeout_sec, 900);
  assert.equal(connector.required, true);
  assert.match(connector.args[2], /releases\/download\/v\$\{version\}/);
  assert.match(connector.args[2], /Checksum verification failed/);
  assert.match(connector.args[2], /cargo install coverage-mcp/);
  assert.match(connector.args[2], /exec \"\$\{runtime_binary\}\" connect$/);
  assert.doesNotMatch(connector.args[2], /daemon\.lock|serve|\/mcp\//);
  const compatibility = JSON.parse(await read('plugins/testing/compatibility.json'));
  assert.equal(compatibility.coverageMcp.schemaRevision, 16);
  assert.equal(compatibility.coverageMcp.toolCount, 8);
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
  assert.equal(compatibility.coverageMcp.bootstrap.manager, 'github-release');
  assert.equal(compatibility.coverageMcp.bootstrap.repository, 'appunni-m/coverage-mcp');
  assert.equal(compatibility.coverageMcp.sharedDaemon.orchestrator, 'coverage-mcp connect');
  assert.equal(compatibility.coverageMcp.connector.workingDirectory, 'inherit-client-project');
  assert.equal(compatibility.coverageMcp.connector.required, true);
  assert.equal(compatibility.coverageMcp.bootstrap.version, '=0.15.3');
  assert.equal(compatibility.coverageMcp.bootstrap.scope, 'exact-binary-acquisition-only');
  assert.equal(compatibility.coverageMcp.bootstrap.customLock, false);
  assert.equal(compatibility.coverageMcp.bootstrap.checksumAsset, 'SHA256SUMS');
  assert.equal(compatibility.coverageMcp.bootstrap.provenance, 'github-sigstore');
  assert.deepEqual(compatibility.coverageMcp.bootstrap.fallback, {
    manager: 'cargo',
    package: 'coverage-mcp',
    version: '=0.15.3',
    locked: true,
  });
  assert.deepEqual(compatibility.coverageMcp.bootstrap.platforms, [
    'macos',
    'linux',
    'wsl',
  ]);
  assert.equal(compatibility.coverageMcp.bootstrap.nativeWindows, false);

  for (const pathname of [
    'README.md',
    'plugins/testing/README.md',
    'plugins/testing/compatibility.json',
    'plugins/testing/.mcp.json',
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

test('Coverage review workflow includes the local dashboard handoff', async () => {
  const skill = await read('plugins/testing/skills/coverage-review/SKILL.md');
  assert.match(skill, /http:\/\/localhost:59471\//);
  assert.match(skill, /after a\s+terminal run/);
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
