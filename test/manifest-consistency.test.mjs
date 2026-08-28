import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const pluginsRoot = path.resolve('plugins');

function configValue(source, field) {
  const match = source.match(new RegExp(`${field}:\\s*(?:\\n\\s*)?'([^']+)'`));
  assert.ok(match, `missing ${field} in aipm.config.ts`);
  return match[1];
}

async function json(pathname) {
  return JSON.parse(await fs.readFile(pathname, 'utf8'));
}

test('authored target manifests match each plugin config', async () => {
  const plugins = await fs.readdir(pluginsRoot, { withFileTypes: true });

  for (const plugin of plugins) {
    if (!plugin.isDirectory()) {
      continue;
    }

    const pluginRoot = path.join(pluginsRoot, plugin.name);
    const config = await fs.readFile(path.join(pluginRoot, 'aipm.config.ts'), 'utf8');
    const version = configValue(config, 'version');
    const description = configValue(config, 'description');

    for (const metadataDirectory of [
      '.claude-plugin',
      '.codex-plugin',
      '.cursor-plugin',
    ]) {
      const manifestPath = path.join(pluginRoot, metadataDirectory, 'plugin.json');
      try {
        const manifest = await json(manifestPath);
        assert.equal(manifest.name, plugin.name, manifestPath);
        const localCodexVersion = `${version}+codex.`;
        assert.ok(
          manifest.version === version ||
            (metadataDirectory === '.codex-plugin' &&
              manifest.version.startsWith(localCodexVersion)),
          `${manifestPath}: ${manifest.version} must match ${version} or use a Codex cachebuster`,
        );
        assert.equal(manifest.description, description, manifestPath);
      } catch (error) {
        if (error.code !== 'ENOENT') {
          throw error;
        }
      }
    }

    const geminiPath = path.join(pluginRoot, 'gemini-extension.json');
    try {
      const manifest = await json(geminiPath);
      assert.equal(manifest.name, plugin.name, geminiPath);
      assert.equal(manifest.version, version, geminiPath);
      assert.equal(manifest.description, description, geminiPath);
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }

    const powerPath = path.join(pluginRoot, 'POWER.md');
    try {
      const power = await fs.readFile(powerPath, 'utf8');
      assert.match(power, new RegExp(`^name: ${plugin.name}$`, 'm'), powerPath);
      assert.match(power, new RegExp(`^version: ${version}$`, 'm'), powerPath);
      assert.match(
        power,
        new RegExp(`^description: ${description.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`, 'm'),
        powerPath,
      );
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
  }
});

test('testing plugin declares and documents its Coverage MCP contract', async () => {
  const pluginRoot = path.join(pluginsRoot, 'testing');
  const compatibility = await json(path.join(pluginRoot, 'compatibility.json'));
  assert.deepEqual(compatibility.coverageMcp, {
    healthUrl: 'http://127.0.0.1:59471/health',
    schemaRevision: 16,
    toolCount: 8,
    toolsSha256: 'd1abfcbc612c4ce09e8ffbfe30849726cc1195f8bee0ff40c33c402ec9d5befa',
    sharedDaemon: {
      orchestrator: 'coverage-mcp connect',
      autoStart: true,
      automaticUpgrade: true,
      survivesConnectorExit: true,
      recoversCrashInExistingConnector: true,
      connectionRefusedReplay: 'once-after-verified-restart',
      ambiguousFailureReplay: false,
      defaultHost: '127.0.0.1',
      defaultPort: 59471,
      ownershipLockFile: '<common-db-parent>/daemon.lock',
      connectionLock: false,
      logFile: '<common-db-parent>/daemon.log',
      projectDatabase: '<canonical-git-root>/.coverage-mcp/coverage.duckdb',
      handoff: {
        authenticated: true,
        preHandoffOwnerFallback: true,
        unknownOwnerPolicy: 'fail-closed',
        downgradePolicy: 'refuse',
      },
    },
    connector: {
      transport: 'stdio',
      command: '/bin/sh',
      argsPrefix: ['-eu', '-c'],
      workingDirectory: 'inherit-client-project',
      required: true,
      versionEnvironment: 'COVERAGE_MCP_VERSION',
      startupTimeoutSeconds: 900,
      runtimeCommand: ['coverage-mcp', 'connect'],
    },
    nativeConnector: {
      command: 'coverage-mcp',
      args: ['connect'],
    },
    bootstrap: {
      manager: 'github-release',
      repository: 'appunni-m/coverage-mcp',
      version: '=0.15.3',
      scope: 'exact-binary-acquisition-only',
      customLock: false,
      platforms: ['macos', 'linux', 'wsl'],
      targets: [
        'aarch64-apple-darwin',
        'x86_64-apple-darwin',
        'aarch64-unknown-linux-gnu',
        'x86_64-unknown-linux-gnu',
      ],
      nativeWindows: false,
      assetPattern: 'coverage-mcp-<version>-<target>.tar.gz',
      checksumAsset: 'SHA256SUMS',
      provenance: 'github-sigstore',
      runtimeDirectoryOverride: 'COVERAGE_MCP_RUNTIME_DIR',
      defaultInstallRoot: '~/.coverage-mcp/runtime/0.15.3',
      fallback: {
        manager: 'cargo',
        package: 'coverage-mcp',
        version: '=0.15.3',
        locked: true,
      },
      releasePrerequisite: 'coverage-mcp 0.15.3 and all claimed native archives published',
    },
    localDevelopment: {
      command: 'cargo',
      args: [
        'run',
        '--locked',
        '--manifest-path',
        '<coverage-mcp-checkout>/Cargo.toml',
        '--',
        'connect',
      ],
    },
  });

  const manifest = await json(path.join(pluginRoot, '.codex-plugin', 'plugin.json'));
  assert.equal(manifest.mcpServers, './.mcp.json');
  const bundledMcp = await json(path.join(pluginRoot, '.mcp.json'));
  const connector = bundledMcp.mcpServers['coverage-mcp'];
  assert.equal(connector.command, compatibility.coverageMcp.connector.command);
  assert.deepEqual(
    connector.args.slice(0, 2),
    compatibility.coverageMcp.connector.argsPrefix,
  );
  assert.equal(connector.args.length, 3);
  assert.equal(connector.cwd, undefined);
  assert.deepEqual(connector.env, {
    [compatibility.coverageMcp.connector.versionEnvironment]:
      compatibility.coverageMcp.bootstrap.version.slice(1),
  });
  assert.equal(
    connector.startup_timeout_sec,
    compatibility.coverageMcp.connector.startupTimeoutSeconds,
  );
  assert.equal(connector.required, compatibility.coverageMcp.connector.required);
  assert.match(connector.args[2], /releases\/download\/v\$\{version\}/);
  assert.match(connector.args[2], /SHA256SUMS/);
  assert.match(connector.args[2], /cargo install coverage-mcp/);
  assert.match(connector.args[2], /exec \"\$\{runtime_binary\}\" connect$/);
  assert.doesNotMatch(connector.args[2], /daemon\.lock|serve|\/mcp\//);

  const geminiManifest = await json(
    path.join(pluginsRoot, 'rust-development', 'gemini-extension.json'),
  );
  assert.deepEqual(
    geminiManifest.mcpServers['coverage-mcp'],
    compatibility.coverageMcp.nativeConnector,
  );

  for (const documentationPath of [
    'README.md',
    path.join(pluginRoot, 'README.md'),
  ]) {
    const documentation = await fs.readFile(documentationPath, 'utf8');
    assert.match(documentation, /coverage[- ]mcp|native Rust executable/i, documentationPath);
    assert.match(documentation, /cargo run --locked/, documentationPath);
    assert.doesNotMatch(documentation, />=0\.6\.0,<0\.7\.0/, documentationPath);
  }

  const geminiContext = await fs.readFile(
    path.join(pluginsRoot, 'rust-development', 'GEMINI.md'),
    'utf8',
  );
  assert.match(geminiContext, /Coverage MCP/);
  assert.match(geminiContext, /human approval/);
  assert.match(geminiContext, /project_context\(detailed=false\)/);

  const skill = await fs.readFile(
    path.join(pluginRoot, 'skills', 'coverage-review', 'SKILL.md'),
    'utf8',
  );
  assert.ok(skill.split('\n').length <= 180, 'Coverage review skill exceeds its context budget');
  assert.ok(skill.trim().split(/\s+/).length <= 1400, 'Coverage review skill is too verbose');
  const normalizedSkill = skill.replace(/\s+/g, ' ');
  for (const requiredGuidance of [
    'human_approved=true',
    'idempotency_key',
    'coverage_ingest',
    'poll_after_ms',
    'run_review',
    'coverage_review',
    'find_duplicate_coverage_tests',
    'coverage_import',
    'BLOCKED_MCP_CONTEXT',
    'latest run',
    'unmeasured',
    'unmeasured coverage',
  ]) {
    assert.ok(normalizedSkill.includes(requiredGuidance), `skill is missing: ${requiredGuidance}`);
  }
});
