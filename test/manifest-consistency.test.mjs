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
        assert.equal(manifest.version, version, manifestPath);
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
    connector: {
      command: 'uvx',
      args: [
        '--from',
        'git+https://github.com/appunni-m/coverage-mcp.git@main',
        'coverage-mcp',
        'connect',
      ],
    },
  });

  const manifest = await json(path.join(pluginRoot, '.codex-plugin', 'plugin.json'));
  assert.deepEqual(manifest.mcpServers['coverage-mcp'], compatibility.coverageMcp.connector);

  const geminiManifest = await json(
    path.join(pluginsRoot, 'rust-development', 'gemini-extension.json'),
  );
  assert.deepEqual(
    geminiManifest.mcpServers['coverage-mcp'],
    compatibility.coverageMcp.connector,
  );

  for (const documentationPath of [
    'README.md',
    path.join(pluginRoot, 'README.md'),
    path.join(pluginRoot, 'skills', 'use-coverage-mcp', 'SKILL.md'),
  ]) {
    const documentation = await fs.readFile(documentationPath, 'utf8');
    assert.match(documentation, /coverage-mcp\.git@main|upstream `main`/, documentationPath);
    assert.doesNotMatch(documentation, />=0\.6\.0,<0\.7\.0/, documentationPath);
    assert.match(documentation, /common_db_path/, documentationPath);
  }

  const geminiContext = await fs.readFile(
    path.join(pluginsRoot, 'rust-development', 'GEMINI.md'),
    'utf8',
  );
  assert.match(geminiContext, /Coverage MCP/);
  assert.match(geminiContext, /human approval/);
  assert.match(geminiContext, /project_context\(detailed=false\)/);

  const skill = await fs.readFile(
    path.join(pluginRoot, 'skills', 'use-coverage-mcp', 'SKILL.md'),
    'utf8',
  );
  assert.ok(skill.split('\n').length <= 180, 'Coverage MCP skill exceeds its context budget');
  assert.ok(skill.trim().split(/\s+/).length <= 1000, 'Coverage MCP skill is too verbose');
  for (const requiredGuidance of [
    'human_approved=true',
    'idempotency_key',
    'coverage_ingest',
    'tools/list',
    '.coverage-mcp/coverage.duckdb',
    'No current worktree snapshot means "not measured", not "unchanged".',
  ]) {
    assert.ok(skill.includes(requiredGuidance), `skill is missing: ${requiredGuidance}`);
  }
});
