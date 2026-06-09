import { defineWorkspace } from '@ai-plugin-marketplace/core';

/**
 * Marketplace metadata for generated host registries. Gemini and Kiro still expose one
 * repository-level artifact, so only rust-development claims those targets.
 */
export default defineWorkspace({
  marketplace: {
    name: 'codegen-marketplace',
    owner: { name: 'Appunni M' },
    description: 'Curated plugins for Rust development, test execution, and coverage analysis',
  },
});
