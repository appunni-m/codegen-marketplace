#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const pluginsRoot = path.resolve('plugins');
const validator = process.platform === 'win32' ? 'skills-ref.cmd' : 'skills-ref';
const skillDirectories = [];
const qualityFailures = [];

for (const plugin of fs.readdirSync(pluginsRoot, { withFileTypes: true })) {
  if (!plugin.isDirectory()) {
    continue;
  }
  const skillsRoot = path.join(pluginsRoot, plugin.name, 'skills');
  if (!fs.existsSync(skillsRoot)) {
    continue;
  }
  for (const skill of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
    const skillDirectory = path.join(skillsRoot, skill.name);
    if (skill.isDirectory() && fs.existsSync(path.join(skillDirectory, 'SKILL.md'))) {
      skillDirectories.push(skillDirectory);
    }
  }
}

skillDirectories.sort();
for (const skillDirectory of skillDirectories) {
  const skillPath = path.join(skillDirectory, 'SKILL.md');
  const skillContent = fs.readFileSync(skillPath, 'utf8');
  const skillLineCount = skillContent.split('\n').length;
  if (skillLineCount > 500) {
    qualityFailures.push(`${skillPath}: ${skillLineCount} lines exceeds the 500-line context budget`);
  }

  const referencesRoot = path.join(skillDirectory, 'references');
  if (fs.existsSync(referencesRoot)) {
    for (const reference of fs.readdirSync(referencesRoot, { withFileTypes: true })) {
      if (!reference.isFile() || !reference.name.endsWith('.md')) {
        continue;
      }
      const referencePath = path.join(referencesRoot, reference.name);
      const referenceContent = fs.readFileSync(referencePath, 'utf8');
      if (referenceContent.split('\n').length > 100 && !/^## Contents$/m.test(referenceContent)) {
        qualityFailures.push(`${referencePath}: references over 100 lines require a Contents section`);
      }
    }
  }

  const result = spawnSync(validator, ['validate', skillDirectory], {
    stdio: 'inherit',
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

if (qualityFailures.length > 0) {
  console.error(qualityFailures.join('\n'));
  process.exit(1);
}

console.log(`Validated ${skillDirectories.length} skill(s).`);
