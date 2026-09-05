import { defineConfig } from '@ai-plugin-marketplace/core';

export default defineConfig({
  version: '0.8.0',
  targets: ['claude', 'codex'],
  description: 'Find coverage gaps and compare existing coverage reports.',
  keywords: ['testing', 'coverage', 'mcp', 'reports', 'quality'],
});
