# Contributing

## Prerequisites

Install Node.js 20 or newer and pnpm 10. After cloning, run:

```bash
pnpm install
```

## Workflow

1. Add or edit a plugin under `plugins/<name>/`. Use `aipm scaffold <name>` to
   create a new one or `aipm add-target <plugin> <target>` to expand an
   existing plugin's support envelope.
2. Run `aipm build` to regenerate toolkit-owned artifacts: hook JSON, the
   `dist/` bundles, marketplace registries, and the repo-root Gemini/Kiro
   artifacts owned by their target plugin.
3. Run `pnpm check`.
4. Commit authored sources and generated output together. CI rebuilds and
   rejects stale generated files.

## Quality Rules

- Keep skills focused and under the Agent Skills progressive-disclosure limit.
- Use current primary sources for changing technical facts.
- Avoid static "latest version" claims.
- Do not add overlapping router skills when one specialist skill can own the
  workflow.
- Do not copy external skill content without a compatible license, preserved
  notices, and clear attribution.
- Record copied or substantially adapted material in the repository-level
  `THIRD_PARTY_NOTICES.md`. If a plugin can be distributed independently, put
  the required notice in that plugin as well.
- Add deterministic tests for executable scripts.
- Keep target versions and descriptions aligned across every authored manifest.

## Target Ownership

Gemini and Kiro each expose one repository-level artifact. Only
`rust-development` currently declares those targets. Add another plugin to
Claude Code, Codex, or Cursor without disturbing that ownership.

## Upgrading the toolkit

```bash
pnpm up @ai-plugin-marketplace/cli @ai-plugin-marketplace/core
pnpm build
pnpm check
```

Review release notes because `0.x` releases may add validation or generated
artifacts even when the authored plugin shape is unchanged.

## Release Checklist

1. Replace development cachebusters and branch-based executable dependencies
   with release versions and immutable tags or commits.
2. Update `CHANGELOG.md`, plugin manifests, compatibility declarations, and
   installation examples together.
3. Run `pnpm install --frozen-lockfile`, `pnpm build`, and `pnpm check`.
4. Confirm `pnpm build` leaves the working tree unchanged except for the
   intended release diff.
5. Review `git diff --check`, `git status --short`, third-party notices, and the
   complete diff against the release base.
6. Create an annotated `vX.Y.Z` tag only after CI passes on the release commit.
