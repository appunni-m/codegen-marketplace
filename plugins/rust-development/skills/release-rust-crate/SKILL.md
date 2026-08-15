---
name: release-rust-crate
description: Prepare, audit, automate, publish, and verify production Rust crate releases to crates.io and GitHub. Use when Codex needs to release a Rust library or binary, choose a SemVer bump, validate MSRV and feature compatibility, inspect Cargo package contents, reduce release risk, publish a first crate, configure GitHub Actions and crates.io Trusted Publishing, secure registry credentials, release a Cargo workspace in dependency order, create immutable tags or binary artifacts, diagnose a failed publish, yank or fix forward, or build a reusable Rust release checklist.
---

# Release Rust Crate

Treat a release as an immutable artifact and evidence chain, not as one Cargo
command. Make the packaged source, registry version, Git tag, generated
documentation, binaries, and release notes identify the same reviewed commit.

## Non-negotiable rules

- Read repository instructions and preserve unrelated changes before editing.
- Separate **prepare/audit** authority from **publish/tag/release** authority.
  Never upload, tag, push, create a GitHub release, add owners, or yank merely
  because the user asked for a review or release plan.
- Never publish from a dirty worktree and never use `--allow-dirty` to bypass
  that release invariant. A dirty package may be inspected, but not uploaded.
- Treat crates.io uploads as permanent. A published name/version cannot be
  overwritten or deleted. Fix forward with a new version; yank only for a
  documented compatibility, correctness, legal, or security reason.
- Never print, copy, commit, log, or persist registry tokens. Prefer crates.io
  Trusted Publishing with a short-lived OIDC token after the manual first
  release. Keep `id-token: write` confined to the publish job.
- Pin third-party GitHub Actions to reviewed full commit SHAs. Keep the human
  release version in an adjacent comment or dependency updater configuration.
- Verify the declared MSRV with that exact toolchain. A current stable build
  does not prove MSRV compatibility.
- Test the features and targets the package claims. `--all-features` alone does
  not prove default or no-default behavior.
- Inspect and build the generated `.crate`; repository tests do not prove that
  required files are present in the published archive.
- Do not move a tag after any registry upload, release, artifact distribution,
  or public announcement refers to it.

## Route the task

For every release, read [crate readiness](references/crate-readiness.md).

Also read:

- [GitHub CI and trusted publishing](references/github-ci-and-publishing.md)
  when creating or reviewing workflows, tags, GitHub Releases, OIDC, action
  permissions, artifacts, checksums, or provenance.
- [Workspaces, first publish, and recovery](references/workspaces-and-recovery.md)
  for multi-crate workspaces, an unclaimed crate name, registry propagation,
  native binary distribution, ownership, a failed upload, a leaked token, a
  bad release, yanking, or rollback/fix-forward decisions.

For a full production-readiness request, read all three references completely.
Use current official Cargo, crates.io, rustdoc, and GitHub documentation for
facts that may have changed; the references contain primary-source links.

## Workflow

### 1. Establish scope and authority

1. Record repository root, target package(s), registry, current revision,
   branch, worktree state, release mode, supported platforms, MSRV, feature
   policy, and whether the package ships a library, CLI, build script, proc
   macro, native library, or external artifact.
2. Identify the user's requested stopping point: audit, prepare, commit, tag,
   publish, create a GitHub Release, or perform post-release verification.
3. Inspect existing manifests, lockfiles, release automation, changelog,
   documentation, package include/exclude rules, licenses, security policy,
   prior tags, and current registry state. Do not infer them from one file.
4. Run the bundled static audit early and again on the exact release commit:

```bash
python3 <skill-root>/scripts/audit_release.py <repository> \
  --expected-version <x.y.z> --strict
```

Use `--format json` for machine-readable evidence. The audit identifies
structural risks; it does not prove API compatibility, test correctness,
credential safety outside the repository, or successful publication.

### 2. Freeze the release contract

1. Classify public API, CLI, configuration, file-format, protocol, feature,
   platform, MSRV, and behavioral changes against the project's documented
   compatibility policy and Cargo's SemVer guidance.
2. Select the version before editing. For `0.y.z`, remember Cargo treats the
   left-most non-zero component as the compatibility boundary.
3. Synchronize every authoritative version source, internal dependency
   requirement, lockfile package row, changelog heading, documentation example,
   generated metadata, and tag plan.
4. Curate release notes around user impact, migration steps, security relevance,
   deprecated behavior, and known limitations. Do not turn a commit list into
   unsupported claims.
5. Make MSRV and supported-target changes explicit. Verify the exact MSRV and
   every platform claim in CI or label unverified support precisely.

### 3. Build the candidate evidence

Use repository-native commands first. A typical crate gate includes:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps --locked
cargo package --list --locked -p <package>
cargo package --locked -p <package>
```

Adapt feature and target matrices to the contract. Add doctests, examples,
MSRV, default/no-default features, platform targets, integration tests,
benchmarks, ABI checks, migration tests, license/advisory policy, or binary
smoke tests when applicable. Do not install optional tools or weaken existing
gates without authorization.

Inspect the package file list, compressed size, normalized manifest, bundled
license/readme/assets, and extracted clean build. Explain every intentional
`--no-verify`; never use it to conceal an unverified archive.

### 4. Require a clean, reviewed release commit

1. Re-run the narrow affected checks after edits and the full project release
   gate before handoff.
2. Commit the version, lockfile, changelog, documentation, workflow, and
   generated files together when the repository expects them together.
3. Confirm `git status --short` is empty and record `git rev-parse HEAD`.
4. Require branch protection and hosted CI on that exact commit before tagging
   or manually publishing. A local pass and a different CI commit are not the
   same evidence.

### 5. Publish through one controlled path

Choose exactly one path:

- **Existing crate with trusted publishing:** push an annotated immutable tag
  only after branch CI passes; let the tag workflow reproduce gates, validate
  tag/version equality, mint the short-lived token, and publish.
- **First crates.io release:** publish the clean, CI-proven commit manually
  with a narrowly scoped short-lived maintainer token; verify registry
  propagation; configure the crate's trusted publisher; then tag that exact
  commit so future releases use OIDC.
- **Authorized manual existing release:** run `cargo publish --locked` from a
  separate clean checkout of the proven commit, then verify before tagging or
  creating downstream releases according to repository policy.

Before retrying any failed or timed-out upload, query the exact version on the
registry. Cargo may time out while waiting for index visibility after the
server has accepted the upload.

### 6. Verify as a consumer

After registry propagation:

1. Query the exact registry version, not only the latest package page.
2. Install or depend on the exact version from an empty temporary Cargo home,
   target directory, and sample project with `--locked` where appropriate.
3. Exercise the smallest public success path, default/no-default features,
   binary `--version`/help, generated docs, and platform artifacts applicable
   to the release.
4. Confirm the registry source, Git tag, checksums, GitHub Release, docs.rs
   build, SBOM/provenance, and downstream pins all identify the intended
   version and commit.
5. Remove or revoke any bootstrap credential as soon as it is no longer
   required. Do not inspect or report its value.

## Stop conditions

Stop before publishing or tagging when any of these remain:

- dirty or ambiguous source state;
- version/tag/changelog/lockfile disagreement;
- unreviewed breaking change or MSRV/platform regression;
- required local or hosted gate not green on the release commit;
- package archive differs from the verified artifact or omits required files;
- unpublished workspace dependency or wrong publish order;
- registry ownership, first-publish token, trusted-publisher configuration, or
  GitHub environment is missing;
- a registry name or tag is occupied by an unknown owner;
- a previous publish result is uncertain and the exact registry version has
  not been checked;
- the requested action exceeds the user's authorization.

Do not call a release production-ready while a stop condition is waived.

## Completion report

Report the exact commit, version, package(s), registry, toolchain/MSRV, target
and feature matrix, commands run, test/doc/package results, `.crate` contents
and size, hosted checks, authentication mode, tag and registry URLs, clean
consumer verification, unsupported claims, skipped checks, and remaining risk.

Distinguish **prepared**, **CI-proven**, **published**, **registry-visible**,
**consumer-verified**, and **released**. These are separate states.
