import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';

const marketplaceRoot = path.resolve(import.meta.dirname, '..');
const coverageCheckout = path.resolve(
  process.env.COVERAGE_MCP_CHECKOUT ?? path.join(marketplaceRoot, '..', 'coverage-mcp'),
);
const binary = process.env.COVERAGE_MCP_BIN ?? 'coverage-mcp';
const compatibility = JSON.parse(
  await fs.readFile(path.join(marketplaceRoot, 'plugins/testing/compatibility.json'), 'utf8'),
);

const request = `${JSON.stringify({
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/list',
})}\n`;

const response = await new Promise((resolve, reject) => {
  const child = spawn(binary, ['connect', '--repo', coverageCheckout], {
    cwd: coverageCheckout,
    env: process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  let stdout = '';
  let stderr = '';
  const timer = setTimeout(() => {
    child.kill('SIGTERM');
    reject(new Error(`timed out waiting for ${binary} tools/list`));
  }, 30_000);
  child.stdout.setEncoding('utf8');
  child.stderr.setEncoding('utf8');
  child.stdout.on('data', (chunk) => {
    stdout += chunk;
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk;
  });
  child.on('error', (error) => {
    clearTimeout(timer);
    reject(new Error(`could not execute ${binary}: ${error.message}`));
  });
  child.on('close', (code, signal) => {
    clearTimeout(timer);
    if (code !== 0) {
      reject(new Error(`${binary} exited with ${code ?? signal}: ${stderr.trim()}`));
      return;
    }
    const line = stdout
      .trim()
      .split(/\r?\n/)
      .reverse()
      .find((candidate) => candidate.trim().startsWith('{'));
    try {
      resolve(JSON.parse(line));
    } catch (error) {
      reject(new Error(`invalid tools/list response: ${error.message}; stderr: ${stderr.trim()}`));
    }
  });
  child.stdin.end(request);
});

const contract = response?.result?.contract;
const expected = compatibility.coverageMcp;
assert.deepEqual(
  contract,
  {
    schema_revision: expected.schemaRevision,
    tool_count: expected.toolCount,
    tools_sha256: expected.toolsSha256,
  },
  'Coverage MCP tools/list contract differs from the marketplace pin',
);
console.log(
  `Coverage MCP contract verified: schema ${contract.schema_revision}, ${contract.tool_count} tools, ${contract.tools_sha256}`,
);
