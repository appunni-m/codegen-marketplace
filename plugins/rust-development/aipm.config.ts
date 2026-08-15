import { defineConfig } from '@ai-plugin-marketplace/core';

export default defineConfig({
  version: '0.3.2',
  targets: ['claude', 'codex', 'cursor', 'gemini', 'kiro', 'vercel'],
  description:
    'Rust engineering guidance for implementation, debugging, documentation, crate research and releases, coding standards, and unsafe review.',
  keywords: ['rust', 'debugging', 'documentation', 'unsafe', 'cargo', 'clippy', 'release'],
});
