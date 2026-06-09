#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const files = ['README.md', 'CONTRIBUTING.md', 'CLAUDE.md'];
const failures = [];

function collectMarkdown(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      collectMarkdown(entryPath);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(entryPath);
    }
  }
}

collectMarkdown('plugins');

for (const file of files.sort()) {
  const content = fs.readFileSync(file, 'utf8');
  const fenceCount = content.split('\n').filter((line) => line.startsWith('```')).length;
  if (fenceCount % 2 !== 0) {
    failures.push(`${file}: unbalanced fenced code blocks`);
  }

  for (const match of content.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
    const target = match[1];
    if (
      target.includes('://') ||
      target.startsWith('#') ||
      target.startsWith('mailto:') ||
      target.startsWith('{')
    ) {
      continue;
    }

    const relativePath = target.split('#', 1)[0];
    if (!relativePath) {
      continue;
    }
    const resolved = path.resolve(path.dirname(file), relativePath);
    if (!fs.existsSync(resolved)) {
      failures.push(`${file}: missing local link target ${target}`);
    }
  }
}

if (failures.length > 0) {
  console.error(failures.join('\n'));
  process.exit(1);
}

console.log(`Validated ${files.length} Markdown file(s).`);
