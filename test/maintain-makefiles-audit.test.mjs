import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const script = path.resolve(
  'plugins/opensource/skills/maintain-makefiles/scripts/audit_makefile.py',
);

async function fixture(files) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'maintain-makefiles-'));
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

test('audit inventories Make command evidence deterministically', async (t) => {
  const root = await fixture({
    Makefile: [
      '.DEFAULT_GOAL := help',
      'BUILD_DIR ?= build',
      '.PHONY: all build test verify update clean help recurse',
      'all: build',
      'build: | $(BUILD_DIR)',
      '\t@touch $(BUILD_DIR)/app',
      '$(BUILD_DIR):',
      '\t@mkdir -p $@',
      'test:',
      '\t@true',
      'verify: test',
      'update:',
      '\t@true',
      'clean:',
      '\t@test -n "$(BUILD_DIR)"',
      '\t@test "$(BUILD_DIR)" != "/"',
      '\t@rm -rf -- "$(BUILD_DIR)"',
      'help:',
      '\t@true',
      'recurse:',
      '\t+$(MAKE) -C sub',
    ].join('\n'),
    'sub/Makefile': '.PHONY: all\nall:\n\t@true\n',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.equal(report.schema_version, 1);
  assert.deepEqual(report.inventory.makefiles, ['Makefile', 'sub/Makefile']);
  assert.equal(report.inventory.default_goal, 'help');
  assert.ok(report.inventory.targets.includes('verify'));
  assert.ok(report.inventory.targets.includes('update'));
  assert.ok(report.inventory.phony_targets.includes('clean'));
  assert.ok(report.inventory.features.includes('order_only_prerequisites'));
  assert.equal(report.summary.errors, 0);
});

test('strict audit flags parse-time execution, unsafe cleanup, and recursive jobserver loss', async (t) => {
  const root = await fixture({
    Makefile: [
      'BUILD_DIR ?=',
      'REV := $(shell git rev-parse --short HEAD)',
      'all:',
      '\tmake -C sub',
      'clean:',
      '\trm -rf $(BUILD_DIR)',
    ].join('\n'),
    'sub/Makefile': 'all:\n\t@true\n',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((finding) => finding.code);

  assert.ok(codes.includes('parse_time_shell'));
  assert.ok(codes.includes('unsafe_clean'));
  assert.ok(codes.includes('literal_recursive_make'));
  assert.ok(codes.includes('missing_phony'));
});

test('audit exposes a claimed POSIX dialect that uses GNU-only syntax', async (t) => {
  const root = await fixture({
    Makefile: [
      '.POSIX:',
      'SOURCES := $(wildcard src/*.c)',
      '.PHONY: all',
      'all: $(SOURCES)',
      '\t@true',
    ].join('\n'),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root, '--strict');
  assert.equal(result.status, 1, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);

  assert.ok(
    report.findings.some((finding) => finding.code === 'posix_dialect_mismatch'),
  );
  assert.equal(report.inventory.declared_dialect, 'posix');
});

test('audit identifies host-derived targets and unscoped multi-platform outputs', async (t) => {
  const root = await fixture({
    Makefile: [
      'TARGET_ARCH := $(shell uname -m)',
      'TARGET_OS ?= $(shell uname -s)',
      'BUILD_DIR ?= build',
      '.PHONY: build',
      'build:',
      '\t@printf "%s/%s\\n" "$(TARGET_OS)" "$(TARGET_ARCH)"',
    ].join('\n'),
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  const codes = report.findings.map((finding) => finding.code);

  assert.deepEqual(report.inventory.platform_variables, [
    'TARGET_ARCH',
    'TARGET_OS',
  ]);
  assert.ok(codes.includes('host_derived_target'));
  assert.ok(codes.includes('unscoped_platform_output'));
  assert.equal(report.summary.errors, 2, 'parse-time shell remains an execution risk');
  assert.ok(report.summary.review >= 2);
});

test('audit rejects a repository without a Makefile', async (t) => {
  const root = await fixture({ 'README.md': '# No Makefile\n' });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = audit(root);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /no Makefile found/);
});

test('text output states that static inventory cannot prove Make semantics', async (t) => {
  const root = await fixture({
    Makefile: '.PHONY: all\nall:\n\t@true\n',
  });
  t.after(() => fs.rm(root, { recursive: true, force: true }));

  const result = spawnSync('python3', [script, root], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Makefile static evidence inventory/);
  assert.match(result.stdout, /does not prove dependency or recipe correctness/);
  assert.match(result.stdout, /Inspect findings before running make/);
});
