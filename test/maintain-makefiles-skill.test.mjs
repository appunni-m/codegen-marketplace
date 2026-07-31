import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/opensource/skills/maintain-makefiles';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

test('Makefile skill stays compact and owns a narrow command contract', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 220, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1400, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: maintain-makefiles$/m);
  assert.match(skill, /^description: .+Makefile.+standardiz.+$/m);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
  assert.match(skill, /Makefile and its contributor-facing command surface/);
  assert.match(skill, /not a general application-code, CI, packaging, or build-system redesign/);
  assert.match(skill, /Preserve working project-native targets/);
  assert.match(skill, /add aliases/);
  assert.match(skill, /Do not replace a repository's native build tool/);
  assert.match(skill, /audit_makefile\.py/);
  assert.match(skill, /static evidence.*does not prove semantic correctness/is);
});

test('skill makes inspection safe before treating Makefiles as commands', async () => {
  const skill = await read('SKILL.md');

  assert.match(skill, /Inspect Makefiles as executable input before invoking Make/);
  assert.match(skill, /parse-time side effects/);
  assert.match(skill, /\$\(shell/);
  assert.match(skill, /included makefiles/);
  assert.match(skill, /make -n.*not a safety boundary/is);
  assert.match(skill, /make -qp/);
  assert.match(skill, /only after static inspection/);
  assert.match(skill, /destructive, networked, privileged, interactive, or publishing/);
});

test('skill standardizes useful targets without inventing a universal standard', async () => {
  const skill = await read('SKILL.md');
  const reference = await read('references/checklist.md');

  for (const target of [
    'all',
    'install',
    'uninstall',
    'clean',
    'distclean',
    'check',
    'installcheck',
    'dist',
    'help',
    'build',
    'test',
    'verify',
    'lint',
    'format',
    'generate',
    'update',
    'package',
    'publish',
  ]) {
    assert.match(reference, new RegExp(`\\b${target}\\b`), `missing target contract: ${target}`);
  }

  assert.match(skill, /GNU Coding Standards.*not universal/is);
  assert.match(skill, /modern aliases.*conventions, not specifications/is);
  assert.match(reference, /read-only.*verify/is);
  assert.match(reference, /source-mutating.*update/is);
  assert.match(reference, /local artifact.*package/is);
  assert.match(reference, /external side effect.*publish/is);
  assert.match(reference, /PREFIX/);
  assert.match(reference, /DESTDIR/);
});

test('checklist catches semantic Make failures that superficial cleanup misses', async () => {
  const skill = await read('SKILL.md');
  const reference = await read('references/checklist.md');

  for (const subtleCheck of [
    '.PHONY',
    'order-only prerequisites',
    '$(MAKE)',
    'jobserver',
    '.ONESHELL',
    '.DELETE_ON_ERROR',
    'secondary expansion',
    'automatic variables',
    'command-line variable',
    'recursive',
    'timestamp',
    'clock skew',
    'intermediate',
  ]) {
    assert.ok(reference.includes(subtleCheck), `missing subtle check: ${subtleCheck}`);
  }

  for (const validation of [
    'default goal',
    'no-op rebuild',
    'selective rebuild',
    'parallel build',
    'failure cleanup',
    'clean safety',
    'variable override',
    'staged install',
  ]) {
    assert.match(reference, new RegExp(validation, 'i'), `missing validation: ${validation}`);
  }

  assert.match(skill, /fresh checkout/);
  assert.match(skill, /second invocation/);
  assert.match(skill, /touch one representative input/);
  assert.match(skill, /parallel/);
  assert.match(skill, /failed recipe/);
});

test('skill treats multi-architecture and multi-system support as an explicit contract', async () => {
  const skill = await read('SKILL.md');
  const reference = await read('references/checklist.md');
  const payload = JSON.parse(await read('evals/evals.json'));
  const platformEval = payload.evals.find((entry) => entry.id === 8);

  assert.match(skill, /multi-architecture/);
  assert.match(skill, /cross-compil/);
  assert.match(skill, /build, host, and target systems/);
  assert.match(skill, /separate output roots/);
  assert.match(skill, /native and cross builds/);

  for (const contract of [
    'build system',
    'host system',
    'target system',
    'TARGET_OS',
    'TARGET_ARCH',
    'canonical',
    'architecture aliases',
    'per-target output',
    'target binary',
    'runner',
    'toolchain',
    'endianness',
    'Linux',
    'macOS',
    'Windows',
    'cross-compilation',
  ]) {
    assert.match(reference, new RegExp(contract, 'i'), `missing platform contract: ${contract}`);
  }

  assert.match(reference, /Do not infer the target exclusively from `uname`/);
  assert.match(reference, /package names.*operating system.*architecture/is);
  assert.match(reference, /native build.*cross build.*artifact inspection/is);
  assert.ok(platformEval, 'missing multi-platform eval');
  assert.match(platformEval.prompt, /amd64.*arm64.*Linux.*macOS.*Windows/is);
  assert.match(platformEval.expected_output, /build, host, and target/is);
  assert.match(platformEval.expected_output, /per-target/is);
  assert.match(platformEval.expected_output, /does not run target binaries/is);
});

test('evals target mistakes a strong general model can miss', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'maintain-makefiles');
  assert.ok(payload.evals.length >= 7);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');

  for (const scenario of [
    'legacy targets',
    'parallel',
    'parse-time',
    'POSIX',
    '.ONESHELL',
    'DESTDIR',
    'only the Makefile',
  ]) {
    assert.match(prompts, new RegExp(scenario, 'i'), `missing eval scenario: ${scenario}`);
  }

  for (const behavior of [
    'aliases',
    'no-op',
    'jobserver',
    'static',
    'dialect',
    'failure',
    'staged install',
    'scope',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing eval behavior: ${behavior}`);
  }
});

test('skill UI metadata explicitly invokes the skill', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Maintain Makefiles"/);
  assert.match(metadata, /short_description: "Standardize and verify reliable Make commands"/);
  assert.match(metadata, /default_prompt: "Use \$maintain-makefiles /);
});
