import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';

test('Coverage MCP contract pointer lists the current public contract', async () => {
  const plan = await fs.readFile('docs/coverage-mcp-contract.md', 'utf8');
  for (const requiredTool of [
    '`project_context`',
    '`register_test_command`',
    '`run_test`',
    '`run_review`',
    '`cancel_run`',
    '`coverage_review`',
    '`find_duplicate_coverage_tests`',
    '`coverage_import`',
  ]) {
    assert.match(plan, new RegExp(requiredTool.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  for (const requiredInvariant of [
    'schema revision 15',
    'composite',
    'approval',
    'polling',
    'freshness',
    'source_resolution',
    'max_bytes',
    'HTTP',
    'stdio',
  ]) {
    assert.match(plan, new RegExp(requiredInvariant));
  }
});
