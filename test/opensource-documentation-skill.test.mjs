import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

const root = 'plugins/opensource/skills/opensource-documentation';

async function read(relativePath) {
  return fs.readFile(`${root}/${relativePath}`, 'utf8');
}

test('open-source documentation skill stays compact and routes to evidence', async () => {
  const skill = await read('SKILL.md');
  const lines = skill.split('\n').length;
  const words = skill.trim().split(/\s+/).length;

  assert.ok(lines <= 250, `SKILL.md has ${lines} lines`);
  assert.ok(words <= 1600, `SKILL.md has ${words} words`);
  assert.match(skill, /^name: opensource-documentation$/m);
  assert.match(skill, /^description: .+README.+public APIs.+open-source release\.$/m);
  assert.doesNotMatch(skill, /\[(?:TODO|TBD)[^\]]*\]/);
  assert.match(skill, /proved.*declared.*planned.*unknown/s);
  assert.match(skill, /Do not use prose to verify copied prose/);
  assert.match(skill, /audit_documentation\.py/);
  assert.match(skill, /The script inventories evidence; it does not prove semantic quality/);
  assert.match(skill, /actual source archive, package, container, installer, or binary/);
  assert.match(skill, /Rank and score only documentation findings/);
  assert.match(skill, /residual documentation debt and risk/);
});

test('documentation audits do not expand into implementation reviews', async () => {
  const skill = await read('SKILL.md');
  const payload = JSON.parse(await read('evals/evals.json'));
  const scopeEval = payload.evals.find((entry) => entry.id === 7);

  assert.match(
    skill,
    /This is a documentation skill, not a general implementation, API-design,\s+security, or maintainability review\./,
  );
  assert.match(skill, /Inspect implementation only as needed to verify documented claims/);
  assert.match(skill, /Rank and score only documentation findings/);
  assert.match(skill, /separate, unranked \*\*Implementation\s+blockers exposed by documentation validation\*\* appendix/);
  assert.match(skill, /Do not\s+recommend implementation changes unless the user also requested/);
  assert.match(skill, /Exclude unrelated code quality, API design, architecture, maintainability,/);
  assert.doesNotMatch(skill, /Improve project quality without hiding defects/);
  assert.doesNotMatch(skill, /Record .* as product defects/);

  assert.ok(scopeEval, 'missing scope-boundary eval');
  assert.match(scopeEval.prompt, /Evaluate only the documentation/);
  assert.match(scopeEval.prompt, /Keep the report within the requested documentation scope/);
  assert.match(scopeEval.expected_output, /Prioritizes and scores only documentation findings/);
  assert.match(scopeEval.expected_output, /does not recommend implementation changes/);
  assert.match(
    scopeEval.expected_output,
    /separate unranked 'Implementation blockers exposed by documentation validation' appendix/,
  );
});

test('exhaustive reference covers reader flow, source contracts, ecosystems, and trust', async () => {
  const reference = await read('references/checklist.md');
  const headings = [...reference.matchAll(/^(#{2,3}) (.+)$/gm)].map((match) => match[2]);
  const languageProfiles = headings.filter((heading) => /^7\.\d+ /.test(heading));
  const readmeFlows = headings.filter(
    (heading) => /^2\.\d+ /.test(heading) && !/Contributor|Maintainer/.test(heading),
  );

  assert.match(reference, /^## Contents$/m);
  assert.ok(languageProfiles.length >= 33, `${languageProfiles.length} language profiles`);
  assert.ok(readmeFlows.length >= 10, `${readmeFlows.length} README flows`);

  const qualityDimensions = new Map([
    ['audience journeys', '## 1. Repository and audience inventory'],
    ['README onboarding', '## 2. README heading flows'],
    ['documentation set', '## 3. Documentation-set coverage'],
    ['source API contracts', '## 4. Source-code documentation'],
    ['document intent', '## 5. Document intent and content checks'],
    ['project profiles', '## 6. Project-type specialties'],
    ['language profiles', '## 7. Language and ecosystem specialties'],
    ['open-source trust', '## 8. Open-source trust, community, and lifecycle'],
    ['accessibility', '## 9. Writing, accessibility, localization, and visual content'],
    ['verification', '## 10. Truth and validation gates'],
    ['failure resistance', '## 11. Failure-mode checklist from observed Codex sessions'],
    ['quality measurement', '## 12. Quality rubric'],
    ['research provenance', '## 13. Authoritative reference index'],
  ]);

  for (const [dimension, heading] of qualityDimensions) {
    assert.ok(reference.includes(heading), `missing ${dimension}`);
  }

  for (const requiredCheck of [
    'Non-circular verification',
    'Package and release-artifact validation',
    'Generated API documentation validation',
    'FFI, native, and ABI documentation',
    'Fresh-reader adversarial review',
    'OpenSSF baseline-aligned checks',
  ]) {
    assert.ok(reference.includes(requiredCheck), `missing ${requiredCheck}`);
  }
});

test('skill evals cover materially different repositories and failure modes', async () => {
  const payload = JSON.parse(await read('evals/evals.json'));
  assert.equal(payload.skill_name, 'opensource-documentation');
  assert.ok(payload.evals.length >= 6);

  const prompts = payload.evals.map((entry) => entry.prompt).join('\n');
  const expected = payload.evals.map((entry) => entry.expected_output).join('\n');

  for (const scenario of [
    'Python CLI',
    'Rust library',
    'self-hosted service',
    'HTTP API',
    'niche language',
    'Do not edit anything',
    'Evaluate only the documentation',
  ]) {
    assert.ok(prompts.includes(scenario), `missing eval scenario: ${scenario}`);
  }
  for (const behavior of [
    'package',
    'public API',
    'security',
    'artifact',
    'authoritative',
    'circular',
  ]) {
    assert.match(expected, new RegExp(behavior, 'i'), `missing eval behavior: ${behavior}`);
  }
});

test('skill UI metadata explicitly invokes the skill', async () => {
  const metadata = await read('agents/openai.yaml');
  assert.match(metadata, /display_name: "Open-Source Documentation"/);
  assert.match(metadata, /short_description: "Create verified, audience-first project docs"/);
  assert.match(metadata, /default_prompt: "Use \$opensource-documentation /);
});
