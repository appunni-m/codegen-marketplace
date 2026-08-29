import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const configPath = new URL('../plugins/testing/.mcp.json', import.meta.url);
const version = '0.15.4';

async function bootstrapScript() {
  const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
  const connector = config.mcpServers['coverage-mcp'];
  assert.equal(connector.command, '/bin/sh');
  assert.deepEqual(connector.args.slice(0, 2), ['-eu', '-c']);
  return connector.args[2];
}

async function temporaryDirectory() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'coverage-mcp-bootstrap-'));
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

async function writeCoverageBinary(pathname, binaryVersion = version) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'if [ "${1:-}" = "--version" ]; then',
      `  printf "%s\\n" "coverage-mcp ${binaryVersion}"`,
      '  exit 0',
      'fi',
      'printf "%s|%s\\n" "$PWD" "$*" >> "${COVERAGE_MCP_PROBE_LOG}"',
    ].join('\n'),
  );
}

async function writeFakeCargo(pathname, exitCode = 0) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'printf "%s\\n" "$*" >> "${FAKE_CARGO_LOG}"',
      'root=""',
      'while [ "$#" -gt 0 ]; do',
      '  if [ "$1" = "--root" ]; then',
      '    shift',
      '    root="$1"',
      '  fi',
      '  shift',
      'done',
      'test -n "${root}"',
      'mkdir -p "${root}/bin"',
      'cp "${FAKE_COVERAGE_MCP_BINARY}" "${root}/bin/coverage-mcp"',
      'chmod 755 "${root}/bin/coverage-mcp"',
      `exit ${exitCode}`,
    ].join('\n'),
  );
}

async function writeFakeUname(pathname) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'case "${1:-}" in',
      '  -s) printf "%s\\n" "${FAKE_UNAME_SYSTEM}" ;;',
      '  -m) printf "%s\\n" "${FAKE_UNAME_MACHINE}" ;;',
      '  *) exit 1 ;;',
      'esac',
    ].join('\n'),
  );
}

async function writeFakeCurl(pathname) {
  await writeExecutable(
    pathname,
    [
      '#!/bin/sh',
      'set -eu',
      'if [ "${FAKE_CURL_FAIL:-0}" = "1" ]; then exit 22; fi',
      'url=""',
      'output=""',
      'while [ "$#" -gt 0 ]; do',
      '  case "$1" in',
      '    http*) url="$1" ;;',
      '    --output) shift; output="$1" ;;',
      '  esac',
      '  shift',
      'done',
      'test -n "${url}"',
      'test -n "${output}"',
      'asset="${url##*/}"',
      'printf "%s\\n" "${url}" >> "${FAKE_CURL_LOG}"',
      'cp "${FAKE_RELEASE_DIR}/${asset}" "${output}"',
    ].join('\n'),
  );
}

async function createRelease(directory, target, checksum = 'valid') {
  const release = path.join(directory, 'release');
  const archiveRoot = path.join(directory, 'archive');
  const archiveDirectory = `coverage-mcp-${version}-${target}`;
  const packagedDirectory = path.join(archiveRoot, archiveDirectory);
  await fs.mkdir(release);
  await fs.mkdir(packagedDirectory, { recursive: true });
  await writeCoverageBinary(path.join(packagedDirectory, 'coverage-mcp'));
  const asset = `${archiveDirectory}.tar.gz`;
  const archive = path.join(release, asset);
  await execFileAsync('tar', ['-C', archiveRoot, '-czf', archive, archiveDirectory]);
  const digest = createHash('sha256').update(await fs.readFile(archive)).digest('hex');
  await fs.writeFile(
    path.join(release, 'SHA256SUMS'),
    `${checksum === 'valid' ? digest : '0'.repeat(64)}  ${asset}\n`,
  );
  return release;
}

function environment(directory, overrides = {}) {
  return {
    HOME: directory,
    PATH: '/usr/bin:/bin',
    COVERAGE_MCP_VERSION: version,
    COVERAGE_MCP_RUNTIME_DIR: path.join(directory, 'runtime'),
    ...overrides,
  };
}

test('uses an exact PATH binary and leaves runtime orchestration to connect', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled bootstrap targets POSIX hosts');
    return;
  }
  const temporary = await temporaryDirectory();
  const project = path.join(temporary.directory, 'project');
  const bin = path.join(temporary.directory, 'bin');
  const probeLog = path.join(temporary.directory, 'probe.log');
  await fs.mkdir(project);
  await fs.mkdir(bin);
  await writeCoverageBinary(path.join(bin, 'coverage-mcp'));

  try {
    await execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
      cwd: project,
      env: environment(temporary.directory, {
        PATH: `${bin}:/usr/bin:/bin`,
        COVERAGE_MCP_PROBE_LOG: probeLog,
      }),
    });
    assert.equal(await fs.readFile(probeLog, 'utf8'), `${await fs.realpath(project)}|connect\n`);
    await assert.rejects(fs.access(path.join(temporary.directory, 'runtime')));
  } finally {
    await temporary.cleanup();
  }
});

for (const [system, machine, target] of [
  ['Darwin', 'arm64', 'aarch64-apple-darwin'],
  ['Darwin', 'x86_64', 'x86_64-apple-darwin'],
  ['Linux', 'aarch64', 'aarch64-unknown-linux-gnu'],
  ['Linux', 'x86_64', 'x86_64-unknown-linux-gnu'],
]) {
  test(`downloads, verifies, and caches the ${target} release`, async (t) => {
    if (process.platform === 'win32') {
      t.skip('the bundled bootstrap targets POSIX hosts');
      return;
    }
    const temporary = await temporaryDirectory();
    const project = path.join(temporary.directory, 'project');
    const bin = path.join(temporary.directory, 'bin');
    const probeLog = path.join(temporary.directory, 'probe.log');
    const curlLog = path.join(temporary.directory, 'curl.log');
    await fs.mkdir(project);
    await fs.mkdir(bin);
    await writeFakeUname(path.join(bin, 'uname'));
    await writeFakeCurl(path.join(bin, 'curl'));
    const release = await createRelease(temporary.directory, target);
    const env = environment(temporary.directory, {
      PATH: `${bin}:/usr/bin:/bin`,
      COVERAGE_MCP_PROBE_LOG: probeLog,
      FAKE_CURL_LOG: curlLog,
      FAKE_RELEASE_DIR: release,
      FAKE_UNAME_SYSTEM: system,
      FAKE_UNAME_MACHINE: machine,
    });

    try {
      await execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
        cwd: project,
        env,
      });
      await execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
        cwd: project,
        env: { ...env, PATH: '/usr/bin:/bin' },
      });

      const asset = `coverage-mcp-${version}-${target}.tar.gz`;
      assert.deepEqual((await fs.readFile(curlLog, 'utf8')).trim().split('\n'), [
        `https://github.com/appunni-m/coverage-mcp/releases/download/v${version}/SHA256SUMS`,
        `https://github.com/appunni-m/coverage-mcp/releases/download/v${version}/${asset}`,
      ]);
      const realProject = await fs.realpath(project);
      assert.equal(
        await fs.readFile(probeLog, 'utf8'),
        `${realProject}|connect\n${realProject}|connect\n`,
      );
      const cached = path.join(temporary.directory, 'runtime', version, 'bin', 'coverage-mcp');
      assert.equal((await fs.stat(cached)).mode & 0o111, 0o111);
    } finally {
      await temporary.cleanup();
    }
  });
}

test('fails closed on a release checksum mismatch without invoking Cargo', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled bootstrap targets POSIX hosts');
    return;
  }
  const temporary = await temporaryDirectory();
  const bin = path.join(temporary.directory, 'bin');
  const template = path.join(temporary.directory, 'coverage-mcp-template');
  const cargoLog = path.join(temporary.directory, 'cargo.log');
  const curlLog = path.join(temporary.directory, 'curl.log');
  await fs.mkdir(bin);
  await writeCoverageBinary(template);
  await writeFakeCargo(path.join(bin, 'cargo'));
  await writeFakeUname(path.join(bin, 'uname'));
  await writeFakeCurl(path.join(bin, 'curl'));
  const release = await createRelease(temporary.directory, 'aarch64-apple-darwin', 'invalid');

  try {
    await assert.rejects(
      execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
        cwd: temporary.directory,
        env: environment(temporary.directory, {
          PATH: `${bin}:/usr/bin:/bin`,
          COVERAGE_MCP_PROBE_LOG: path.join(temporary.directory, 'probe.log'),
          FAKE_CARGO_LOG: cargoLog,
          FAKE_COVERAGE_MCP_BINARY: template,
          FAKE_CURL_LOG: curlLog,
          FAKE_RELEASE_DIR: release,
          FAKE_UNAME_SYSTEM: 'Darwin',
          FAKE_UNAME_MACHINE: 'arm64',
        }),
      }),
      /Checksum verification failed/,
    );
    await assert.rejects(fs.access(cargoLog));
  } finally {
    await temporary.cleanup();
  }
});

test('falls back to an exact Cargo install when release download is unavailable', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled bootstrap targets POSIX hosts');
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
  await writeFakeUname(path.join(bin, 'uname'));
  await writeFakeCurl(path.join(bin, 'curl'));

  try {
    await execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
      cwd: temporary.directory,
      env: environment(temporary.directory, {
        PATH: `${bin}:/usr/bin:/bin`,
        COVERAGE_MCP_PROBE_LOG: probeLog,
        FAKE_CARGO_LOG: cargoLog,
        FAKE_COVERAGE_MCP_BINARY: template,
        FAKE_CURL_FAIL: '1',
        FAKE_CURL_LOG: path.join(temporary.directory, 'curl.log'),
        FAKE_RELEASE_DIR: temporary.directory,
        FAKE_UNAME_SYSTEM: 'Darwin',
        FAKE_UNAME_MACHINE: 'arm64',
      }),
    });
    assert.equal(
      await fs.readFile(cargoLog, 'utf8'),
      `install coverage-mcp --version =${version} --locked --bin coverage-mcp --root ${path.join(
        temporary.directory,
        'runtime',
        version,
      )}\n`,
    );
    assert.equal(
      await fs.readFile(probeLog, 'utf8'),
      `${await fs.realpath(temporary.directory)}|connect\n`,
    );
  } finally {
    await temporary.cleanup();
  }
});

test('accepts a valid runtime produced by a racing Cargo fallback', async (t) => {
  if (process.platform === 'win32') {
    t.skip('the bundled bootstrap targets POSIX hosts');
    return;
  }
  const temporary = await temporaryDirectory();
  const bin = path.join(temporary.directory, 'bin');
  const template = path.join(temporary.directory, 'coverage-mcp-template');
  const probeLog = path.join(temporary.directory, 'probe.log');
  await fs.mkdir(bin);
  await writeCoverageBinary(template);
  await writeFakeCargo(path.join(bin, 'cargo'), 1);
  await writeFakeUname(path.join(bin, 'uname'));

  try {
    await execFileAsync('/bin/sh', ['-eu', '-c', await bootstrapScript()], {
      cwd: temporary.directory,
      env: environment(temporary.directory, {
        PATH: `${bin}:/usr/bin:/bin`,
        COVERAGE_MCP_PROBE_LOG: probeLog,
        FAKE_CARGO_LOG: path.join(temporary.directory, 'cargo.log'),
        FAKE_COVERAGE_MCP_BINARY: template,
        FAKE_UNAME_SYSTEM: 'unsupported',
        FAKE_UNAME_MACHINE: 'unsupported',
      }),
    });
    assert.equal(
      await fs.readFile(probeLog, 'utf8'),
      `${await fs.realpath(temporary.directory)}|connect\n`,
    );
  } finally {
    await temporary.cleanup();
  }
});

test('connector config has no project-changing cwd or second lifecycle lock', async () => {
  const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
  const connector = config.mcpServers['coverage-mcp'];
  assert.equal(connector.cwd, undefined);
  assert.equal(connector.required, true);
  assert.equal(connector.env.COVERAGE_MCP_VERSION, version);
  assert.doesNotMatch(connector.args[2], /\.lock|serve|daemon|\/mcp\//i);
  assert.match(connector.args[2], /releases\/download\/v\$\{version\}/);
  assert.match(connector.args[2], /Checksum verification failed/);
  assert.match(connector.args[2], /cargo install coverage-mcp/);
  assert.match(connector.args[2], /exec \"\$\{runtime_binary\}\" connect$/);
});
