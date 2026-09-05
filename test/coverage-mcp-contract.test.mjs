import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

test('contract pointer stays discoverable and compatibility digest is valid', async () => {
  const guide = await fs.readFile('docs/coverage-mcp-contract.md', 'utf8');
  const { coverageMcp: contract } = JSON.parse(await fs.readFile('plugins/testing/compatibility.json', 'utf8'));
  assert.ok(guide.length < 8000, 'Contract pointer must not duplicate the server manual');
  assert.equal(contract.schemaRevision, 18);
  assert.equal(contract.toolCount, 2);
  assert.match(contract.toolsSha256, /^[a-f0-9]{64}$/);
});
