import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/testing/skills/run-coverage-campaign';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

test('coverage campaign skill owns explicit model routing and one writer', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 220, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1500, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: run-coverage-campaign$/m);
  assert.match(skill, /gpt-5\.6-luna.*reasoning effort `max`/s);
  assert.match(skill, /gpt-5\.6-sol/);
  assert.match(skill, /reasoning effort `high`/);
  assert.match(skill, /fork_turns="none"/);
  assert.match(skill, /main Luna agent as the only writer/);
  assert.match(skill, /Do not delegate edits/);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
});

test('campaign fails closed on foreign Coverage MCP context and weak evidence', async () => {
  const skill = await read('SKILL.md');

  for (const contract of [
    'project_context(detailed=false)',
    'BLOCKED_MCP_CONTEXT',
    'baseline snapshot ID',
    'idempotency_key',
    'successful artifact ingestion',
    'explicit current snapshot ID',
    'Do not claim per-case attribution',
    'human_approved=true',
  ]) {
    assert.ok(skill.includes(contract), `missing campaign contract: ${contract}`);
  }

  assert.match(skill, /do not silently replace managed evidence with raw commands/i);
  assert.match(skill, /Never claim a target percentage from changed denominators/);
});

test('campaign uses a bounded 100-case strategy and Sol recovery loop', async () => {
  const skill = await read('SKILL.md');
  const packets = await read('references/packet-contracts.md');

  assert.match(skill, /100 candidate inputs grouped into 10 coherent\s+families of 10/);
  assert.match(skill, /NEEDS_SOL/);
  assert.match(skill, /at most two Sol revision\s+cycles/);
  assert.match(skill, /entire proposed batch before fixing discovered product bugs/);
  assert.match(skill, /no unique\s+covered line, branch, function, or region/);

  for (const schema of [
    'coverage-campaign/strategy-request@1',
    'coverage-campaign/strategy@1',
    'coverage-campaign/needs-sol@1',
  ]) {
    assert.ok(packets.includes(schema), `missing packet schema: ${schema}`);
  }
  assert.match(packets, /expected_regions.*never expected\s+program output/s);
  assert.match(packets, /validation_lanes/);
  assert.match(packets, /never invent a command or target name/);
  assert.match(packets, /Use `unmeasured`/);
});

test('evals cover routing, evidence failures, pruning, and escalation', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'run-coverage-campaign');
  assert.ok(payload.evals.length >= 12);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');

  for (const scenario of [
    'Sol Max',
    'project_context',
    '100 public inputs',
    'internal enum',
    '20 failures',
    'batch-level snapshot',
    '16-bit input',
    'skipped_stale',
    'five Luna writers',
    'not registered',
    '40,000-line test log',
  ]) {
    assert.match(prompts, new RegExp(scenario, 'i'), `missing eval scenario: ${scenario}`);
  }

  for (const behavior of [
    'sole writer',
    'BLOCKED_MCP_CONTEXT',
    '10 coherent families of 10',
    'unsupported or unreachable',
    'bounded Luna fix',
    'zero-gain',
    'per-case uniqueness',
    'NEEDS_SOL',
    'no improvement claim',
    'human_approved=true',
    'no inherited history',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing expected behavior: ${behavior}`);
  }
});

test('skill UI metadata invokes the model-routed campaign', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Run Coverage Campaign"/);
  assert.match(metadata, /short_description: "Route coverage strategy to Sol and execution to Luna"/);
  assert.match(metadata, /default_prompt: "Use \$run-coverage-campaign /);
});
