import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const launcher = path.join(
  repositoryRoot,
  'plugins',
  'testing',
  'bin',
  'coverage-mcp-launcher',
);

async function temporaryDirectory() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'coverage-mcp-launcher-'));
  return {
    directory,
    async cleanup() {
      await fs.rm(directory, { recursive: true, force: true });
    },
  };
}

async function writeExecutable(pathname, source) {
  await fs.writeFile(pathname, `${source}\n`, { mode: 0o755 });
  await fs.chmod(pathname, 0o755);
}

async function writeCoverageBinary(pathname) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'if [ "${1:-}" = "--version" ]; then',
      '  printf "%s\\n" "coverage-mcp 0.9.0"',
      '  exit 0',
      'fi',
      'printf "%s\\n" "$*" >> "${COVERAGE_MCP_PROBE_LOG}"',
    ].join('\n'),
  );
}

async function writeFakeCargo(pathname) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'printf "%s\\n" "$*" >> "${FAKE_CARGO_LOG}"',
      'printf "%s\\n" "fake Cargo progress"',
      'root=""',
      'while [ "$#" -gt 0 ]; do',
      '  case "$1" in',
      '    --root)',
      '      shift',
      '      root="$1"',
      '      ;;',
      '  esac',
      '  shift',
      'done',
      'test -n "${root}"',
      'sleep "${FAKE_CARGO_DELAY:-0}"',
      'mkdir -p "${root}/bin"',
      'cp "${FAKE_COVERAGE_MCP_BINARY}" "${root}/bin/coverage-mcp"',
      'chmod 755 "${root}/bin/coverage-mcp"',
    ].join('\n'),
  );
}

function launcherEnvironment(directory, overrides = {}) {
  return {
    HOME: directory,
    PATH: '/usr/bin:/bin',
    COVERAGE_MCP_VERSION: '0.9.0',
    COVERAGE_MCP_RUNTIME_DIR: path.join(directory, 'runtime'),
    COVERAGE_MCP_BOOTSTRAP_TIMEOUT_SECONDS: '10',
    ...overrides,
  };
}

test('uses an exact Coverage MCP binary from PATH without bootstrapping', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled launcher is POSIX');
    return;
  }
  const temporary = await temporaryDirectory();
  const bin = path.join(temporary.directory, 'bin');
  const probeLog = path.join(temporary.directory, 'probe.log');
  await fs.mkdir(bin);
  await writeCoverageBinary(path.join(bin, 'coverage-mcp'));

  try {
    await execFileAsync(launcher, ['--repo', '/workspace/project'], {
      env: launcherEnvironment(temporary.directory, {
        HOME: '',
        PATH: `${bin}:/usr/bin:/bin`,
        COVERAGE_MCP_BOOTSTRAP_TIMEOUT_SECONDS: 'invalid-but-unused',
        COVERAGE_MCP_RUNTIME_DIR: '',
        COVERAGE_MCP_PROBE_LOG: probeLog,
      }),
    });
    assert.equal(await fs.readFile(probeLog, 'utf8'), 'connect --repo /workspace/project\n');
    await assert.rejects(fs.access(path.join(temporary.directory, 'runtime')));
  } finally {
    await temporary.cleanup();
  }
});

test('installs the pinned crate once and reuses the cached binary', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled launcher is POSIX');
    return;
  }
  const temporary = await temporaryDirectory();
  const bin = path.join(temporary.directory, 'bin');
  const template = path.join(temporary.directory, 'coverage-mcp-template');
  const cargoLog = path.join(temporary.directory, 'cargo.log');
  const probeLog = path.join(temporary.directory, 'probe.log');
  await fs.mkdir(bin);
  await writeCoverageBinary(template);
  await writeFakeCargo(path.join(bin, 'cargo'));
  const environment = launcherEnvironment(temporary.directory, {
    PATH: `${bin}:/usr/bin:/bin`,
    COVERAGE_MCP_PROBE_LOG: probeLog,
    FAKE_CARGO_LOG: cargoLog,
    FAKE_COVERAGE_MCP_BINARY: template,
  });

  try {
    const firstLaunch = await execFileAsync(launcher, [], { env: environment });
    assert.equal(firstLaunch.stdout, '');
    assert.match(firstLaunch.stderr, /fake Cargo progress/);
    await execFileAsync(launcher, ['--repo', '/workspace/second'], {
      env: { ...environment, PATH: '/usr/bin:/bin' },
    });

    const cargoCalls = (await fs.readFile(cargoLog, 'utf8')).trim().split('\n');
    assert.equal(cargoCalls.length, 1);
    assert.match(
      cargoCalls[0],
      /^install coverage-mcp --version =0\.9\.0 --locked --bin coverage-mcp --root /,
    );
    assert.equal(
      await fs.readFile(probeLog, 'utf8'),
      'connect\nconnect --repo /workspace/second\n',
    );
    await fs.access(
      path.join(temporary.directory, 'runtime', '0.9.0', 'bin', 'coverage-mcp'),
    );
  } finally {
    await temporary.cleanup();
  }
});

test('concurrent first sessions share one bootstrap installation', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled launcher is POSIX');
    return;
  }
  const temporary = await temporaryDirectory();
  const bin = path.join(temporary.directory, 'bin');
  const template = path.join(temporary.directory, 'coverage-mcp-template');
  const cargoLog = path.join(temporary.directory, 'cargo.log');
  const probeLog = path.join(temporary.directory, 'probe.log');
  await fs.mkdir(bin);
  await writeCoverageBinary(template);
  await writeFakeCargo(path.join(bin, 'cargo'));
  const environment = launcherEnvironment(temporary.directory, {
    PATH: `${bin}:/usr/bin:/bin`,
    COVERAGE_MCP_PROBE_LOG: probeLog,
    FAKE_CARGO_DELAY: '1',
    FAKE_CARGO_LOG: cargoLog,
    FAKE_COVERAGE_MCP_BINARY: template,
  });

  try {
    await Promise.all([
      execFileAsync(launcher, ['--repo', '/workspace/a'], { env: environment }),
      execFileAsync(launcher, ['--repo', '/workspace/b'], { env: environment }),
    ]);

    const cargoCalls = (await fs.readFile(cargoLog, 'utf8')).trim().split('\n');
    assert.equal(cargoCalls.length, 1);
    const launches = (await fs.readFile(probeLog, 'utf8')).trim().split('\n').sort();
    assert.deepEqual(launches, [
      'connect --repo /workspace/a',
      'connect --repo /workspace/b',
    ]);
  } finally {
    await temporary.cleanup();
  }
});

test('fails clearly when neither an exact binary nor Cargo is available', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled launcher is POSIX');
    return;
  }
  const temporary = await temporaryDirectory();
  try {
    await assert.rejects(
      execFileAsync(launcher, [], {
        env: launcherEnvironment(temporary.directory),
      }),
      /Coverage MCP 0\.9\.0 is not installed and Cargo is unavailable/,
    );
  } finally {
    await temporary.cleanup();
  }
});

test('fails clearly when the MCP configuration omits the release version', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled launcher is POSIX');
    return;
  }
  const temporary = await temporaryDirectory();
  try {
    await assert.rejects(
      execFileAsync(launcher, [], {
        env: launcherEnvironment(temporary.directory, {
          COVERAGE_MCP_VERSION: '',
        }),
      }),
      /COVERAGE_MCP_VERSION must be a stable x\.y\.z release supplied by the MCP configuration/,
    );
  } finally {
    await temporary.cleanup();
  }
});
