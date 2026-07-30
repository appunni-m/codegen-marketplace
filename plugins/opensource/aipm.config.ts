import { defineConfig } from '@ai-plugin-marketplace/core';

export default defineConfig({
  version: '0.1.0',
  targets: ['claude', 'codex', 'cursor', 'vercel'],
  description:
    'Evidence-first documentation guidance for audience journeys, public APIs, open-source trust, and release artifacts.',
  keywords: ['documentation', 'readme', 'open-source', 'api', 'quality'],
});
