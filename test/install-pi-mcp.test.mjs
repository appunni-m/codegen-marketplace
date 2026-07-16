import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const installer = path.join(
  repositoryRoot,
  'plugins',
  'testing',
  'scripts',
  'install-pi-mcp.mjs',
);

async function temporaryConfig() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'coverage-mcp-pi-'));
  return {
    directory,
    path: path.join(directory, 'mcp.json'),
    async cleanup() {
      await fs.unlink(this.path).catch(() => {});
      await fs.rmdir(this.directory);
    },
  };
}

test('merges coverage-mcp without replacing existing configuration', async () => {
  const config = await temporaryConfig();
  await fs.writeFile(
    config.path,
    JSON.stringify({
      settings: { toolPrefix: 'short' },
      mcpServers: { existing: { command: 'example-server' } },
    }),
  );

  try {
    await execFileAsync(process.execPath, [
      installer,
      '--config',
      config.path,
      '--source',
      'git+https://example.com/coverage-mcp.git@branch',
    ]);

    const result = JSON.parse(await fs.readFile(config.path, 'utf8'));
    assert.deepEqual(result.settings, { toolPrefix: 'short' });
    assert.deepEqual(result.mcpServers.existing, { command: 'example-server' });
    assert.deepEqual(result.mcpServers['coverage-mcp'], {
      command: 'uvx',
      args: [
        '--from',
        'git+https://example.com/coverage-mcp.git@branch',
        'coverage-mcp',
        'connect',
      ],
      lifecycle: 'lazy',
    });

    if (process.platform !== 'win32') {
      const mode = (await fs.stat(config.path)).mode & 0o777;
      assert.equal(mode, 0o600);
    }
  } finally {
    await config.cleanup();
  }
});

test('creates a new shared MCP configuration', async () => {
  const config = await temporaryConfig();
  try {
    await execFileAsync(process.execPath, [installer, '--config', config.path]);
    const result = JSON.parse(await fs.readFile(config.path, 'utf8'));
    assert.deepEqual(result, {
      mcpServers: {
        'coverage-mcp': {
          command: 'uvx',
          args: [
            '--from',
            'git+https://github.com/appunni-m/coverage-mcp.git@main',
            'coverage-mcp',
            'connect',
          ],
          lifecycle: 'lazy',
        },
      },
    });
  } finally {
    await config.cleanup();
  }
});

test('does not overwrite malformed JSON', async () => {
  const config = await temporaryConfig();
  await fs.writeFile(config.path, '{not-json');

  try {
    await assert.rejects(
      execFileAsync(process.execPath, [installer, '--config', config.path]),
      /Cannot parse MCP config/,
    );
    assert.equal(await fs.readFile(config.path, 'utf8'), '{not-json');
  } finally {
    await config.cleanup();
  }
});

test('prints command help', async () => {
  const { stdout } = await execFileAsync(process.execPath, [installer, '--help']);
  assert.match(stdout, /Usage: install-pi-mcp\.mjs/);
  assert.match(stdout, /--config/);
  assert.match(stdout, /--source/);
});
