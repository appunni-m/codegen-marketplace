# GitHub CI and crates.io Trusted Publishing

Use this reference when a release involves GitHub Actions, tags, crates.io
Trusted Publishing, GitHub Releases, binary artifacts, checksums, or build
provenance.

## Contents

1. Trust boundaries
2. Validation workflow
3. Tag and version authority
4. Release workflow architecture
5. Trusted Publishing and first-release boundary
6. Actions supply-chain hardening
7. Artifacts, GitHub Releases, and attestations
8. Reliability and autorecovery
9. Workflow review checklist
10. Primary sources

## 1. Trust boundaries

Separate untrusted validation from privileged publication:

- Pull-request and branch jobs compile and test with `permissions: contents:
  read` or `permissions: {}` plus only the minimum job-specific grants.
- Never expose registry credentials, OIDC minting, environment secrets, or
  write-capable repository tokens to pull-request code.
- Keep the publish job dependent on all required verification/package jobs.
- Give only the publish job `id-token: write`; that permission enables an OIDC
  token request but does not itself grant registry or repository write access.
- Put publication behind a dedicated GitHub environment such as `crates-io`.
  Configure environment tag restrictions and, where appropriate, required
  reviewers or deployment protection rules.
- Give GitHub Release creation or tag mutation a separate job with narrowly
  scoped `contents: write`. Publishing a crate does not require that grant.
- Treat build scripts, tests, proc macros, dependencies, action code, and
  checked-in release scripts as code that can access the permissions of their
  job. Mint credentials only after untrusted build execution has finished.

Do not use `pull_request_target` to build or run untrusted pull-request code in
a privileged context.

## 2. Validation workflow

A branch/PR workflow should make the candidate reproducible before any tag:

- pin the Rust toolchain and test the exact declared MSRV;
- check formatting, strict lints, tests, doctests, rustdoc, feature modes,
  supported targets, migrations/protocols, advisory/license policy, and
  repository-specific gates;
- run `cargo package --locked` and retain or identify the verified `.crate`;
- build distributable binaries with the release profile and target matrix;
- inspect generated artifacts and produce checksums/evidence;
- use explicit timeouts, cancellation/concurrency policy, bounded build jobs,
  and retained failure diagnostics;
- keep permissions read-only and do not make publication depend on hidden local
  state.

Require the default branch's exact release commit to pass. A tag workflow may
reproduce all gates or consume immutable artifacts from a trusted workflow, but
must not treat a similarly named artifact from another commit as evidence.

## 3. Tag and version authority

Choose and document one tag convention, commonly `v<package-version>` for a
single-package repository. The workflow must verify:

- the tag syntax is stable and contains no unexpected pre-release/build data;
- the tag's version equals the selected package version from `cargo metadata`;
- `Cargo.lock`, changelog, generated metadata, and CLI/version constants agree;
- the tag points at a commit that passed required branch protection;
- the same tag/release/version is not already published or occupied by an
  unexpected owner.

Use annotated release tags unless repository policy explicitly requires signed
tags. Never make a movable major tag the identity of a crate release. Never
retarget a tag after an upload or public artifact refers to it.

For a multi-package repository, use an unambiguous convention such as
`<package>-v<version>` and validate the selected package explicitly.

## 4. Release workflow architecture

Prefer isolated jobs with explicit dependencies:

1. **quality** — version/tag assertion, format, lints, rustdoc;
2. **tests** — tests, doctests, features, targets, integration and migrations;
3. **package** — clean `cargo package --locked`, package inventory, archive;
4. **binaries** — release matrix, platform smoke tests, archives;
5. **supply chain** — advisory/license/source policy, SBOM as applicable;
6. **evidence** — checksums, test/package metadata, provenance inputs;
7. **publish** — depends on every required gate, enters protected environment,
   mints short-lived crates.io token, uploads exact package;
8. **release** — creates GitHub Release and uploads verified binary artifacts
   only after publication and registry verification when policy requires it.

Use a skeleton like this, replacing every action placeholder with a reviewed
full commit SHA:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<full-commit-sha> # vX.Y.Z
      - uses: dtolnay/rust-toolchain@<full-commit-sha> # reviewed revision
        with:
          toolchain: <exact-msrv-or-policy-toolchain>
          components: rustfmt, clippy
      - run: test "${GITHUB_REF_NAME#v}" = "$(cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version')"
      - run: cargo fmt --all -- --check
      - run: cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
      - run: cargo test --workspace --all-targets --all-features --locked
      - run: RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps --locked
      - run: cargo package --locked -p <package>

  publish:
    needs: verify
    runs-on: ubuntu-latest
    timeout-minutes: 10
    environment: crates-io
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<full-commit-sha> # vX.Y.Z
      - uses: dtolnay/rust-toolchain@<full-commit-sha> # reviewed revision
        with:
          toolchain: <exact-release-toolchain>
      - name: Authenticate to crates.io
        id: crates-io-auth
        uses: rust-lang/crates-io-auth-action@<full-commit-sha> # vX.Y.Z
      - name: Publish
        run: cargo publish --locked -p <package>
        env:
          CARGO_REGISTRY_TOKEN: ${{ steps.crates-io-auth.outputs.token }}
```

Adapt the matrix and package selection. The skeleton does not prove that one
job's package is exactly the archive uploaded by another job. For strong
provenance, transfer and validate the verified archive or reproduce it from the
same tag with checksums and deterministic inputs.

### `--no-verify`

Cargo normally packages, extracts, and builds before upload. Use
`cargo publish --no-verify` only when a prior isolated job already verified the
same archive/source and publication would otherwise repeat an exceptionally
expensive build after credential minting. Document the artifact boundary and
keep the publish job dependent on that gate. Never use `--no-verify` merely to
make a broken package upload.

### Idempotent retry

Before publishing, query `crate@version`:

- if absent, publish;
- if present and it is the intended immutable release, skip duplicate upload
  and continue verification/artifact assembly;
- if the query fails for an unrelated network/authentication reason, fail
  rather than guessing;
- after a publish timeout, query again before retrying because the upload may
  have succeeded while index polling timed out.

## 5. Trusted Publishing and first-release boundary

crates.io Trusted Publishing uses a GitHub OIDC identity to mint a short-lived
registry token. Configure the crate on crates.io with the exact:

- GitHub owner/organization;
- repository;
- workflow filename under `.github/workflows/`;
- optional GitHub environment name, which must match the job.

The workflow needs `id-token: write`, calls the official
`rust-lang/crates-io-auth-action`, and passes its token output only to the
publish step through `CARGO_REGISTRY_TOKEN`. The action revokes the temporary
token in its post step.

Trusted Publishing cannot bootstrap an unclaimed crate because the publisher
configuration is attached to an existing crate. Publish the first version
manually from the clean, CI-proven commit with a narrowly scoped maintainer API
token. Then:

1. verify the exact version is registry-visible and consumer-installable;
2. configure the trusted publisher for future versions;
3. revoke/logout the bootstrap token when no longer needed;
4. tag the exact published commit according to repository policy;
5. test the tag workflow's authentication without attempting a duplicate
   version, or let it detect and skip that exact already-published version.

Never store a long-lived crates.io token in GitHub Actions when Trusted
Publishing is available. Never commit Cargo credential files. If a local token
must be used, remember Cargo's token credential provider can store it as plain
text in the Cargo credentials file; protect, minimize, and remove it.

## 6. Actions supply-chain hardening

- Pin every external action to a 40-character commit SHA. Tags and branches can
  move. Keep a comment such as `# v4.3.0` for reviewers and dependency bots.
- Verify the SHA belongs to the intended upstream release using the upstream
  repository, signed release information when available, and organizational
  allowlisting policy.
- Configure Dependabot/Renovate to propose reviewed action updates rather than
  using a movable reference.
- Explicitly set workflow and job permissions. Do not rely on repository
  defaults.
- Restrict which actions and reusable workflows the organization permits.
- Avoid untrusted dynamic action names, mutable containers, curl-to-shell, and
  generated workflow code in privileged jobs.
- Do not persist checkout credentials unless a later step must push; publication
  itself does not require them.
- Avoid command construction from tag, branch, issue, or PR text. Validate and
  quote untrusted context before passing it to a shell.
- Use environments and tag restrictions for publication. Treat workflow file
  changes as security-sensitive code review.
- Put network-heavy, compiler-heavy, and untrusted build steps before OIDC token
  minting. Keep the token lifetime and exposure window short.
- Never echo `${{ steps.<auth>.outputs.token }}`, enable shell tracing around
  it, upload environments, or include credential/config directories in
  artifacts.

## 7. Artifacts, GitHub Releases, and attestations

For source-only crates, the registry package and tag may be the complete
release. For native binaries or additional artifacts:

- build each claimed target in an explicit matrix;
- test on the target platform when possible; distinguish cross-compilation from
  runtime verification;
- archive predictable file names containing package, version, target, and
  compression format;
- include license/readme/notices and generate checksums after final packaging;
- record compiler/toolchain, target, source commit, features, and build flags;
- upload only artifacts from required jobs and fail on missing files;
- consider SBOMs, signatures, and GitHub artifact attestations for provenance;
- verify downloaded artifacts and checksums from a clean environment before
  publishing the GitHub Release.

GitHub artifact attestations require additional job permissions. Grant them
only to the attestation job and follow the current official documentation.
Attestation establishes build provenance; it does not prove correctness or
absence of vulnerabilities.

If creating a GitHub Release, use the immutable version tag, curated release
notes, checksums, and supported artifacts. Keep `contents: write` in this job,
not in general validation or crates.io publication.

## 8. Reliability and autorecovery

- Use concurrency intentionally. Branch validation may cancel superseded runs;
  a tag/release workflow should not silently cancel a different immutable tag.
- Add realistic job timeouts. After splitting compile and runtime phases, bound
  each so a disconnected runner cannot retain a serialized release slot for
  hours.
- Bound test polling and child-process shutdown. Retain the exact target's logs
  on failure.
- Split expensive compile, test groups, coverage, package verification, and
  release builds when one hosted runner can be starved or lose communication.
- Cap Cargo build jobs on memory-constrained runners when linking native or
  debug-heavy dependencies. Reduce unnecessary debug info for test profiles
  only with an understood diagnostics tradeoff.
- Cache downloads/builds for speed, but require clean package and consumer
  checks that do not mistake a warm cache for a release prerequisite.
- Make publish retries registry-aware and idempotent. Do not delete tags,
  packages, locks, or artifacts as an automatic recovery shortcut.
- Upload failure diagnostics with `if: failure()` and make evidence uploads fail
  if required evidence is absent.

## 9. Workflow review checklist

- [ ] Tag trigger and tag/version/package selection are exact.
- [ ] All third-party actions use reviewed full SHAs.
- [ ] Default permissions are read-only or empty.
- [ ] Pull-request code never reaches publish credentials or OIDC.
- [ ] Verification runs before the publish environment/token.
- [ ] The publish job needs all mandatory gates.
- [ ] `id-token: write` exists only where required.
- [ ] The GitHub environment matches crates.io publisher configuration.
- [ ] `CARGO_REGISTRY_TOKEN` comes from the auth step output, not secrets or a
      literal.
- [ ] `cargo publish` is locked, selects the intended package/registry, and has
      no dirty bypass.
- [ ] Any `--no-verify` has same-artifact evidence.
- [ ] Already-published and timeout retry behavior is explicit.
- [ ] Workspaces publish in dependency order with propagation checks.
- [ ] Jobs have bounded resources/timeouts and retained diagnostics.
- [ ] Binary/source artifacts, checksums, and attestations share one commit.
- [ ] GitHub Release write permission is isolated.
- [ ] No token, credential directory, runner environment, or private data is
      logged or uploaded.

## 10. Primary sources

- [crates.io authentication action](https://github.com/rust-lang/crates-io-auth-action)
- [Rust RFC 3691: crates.io Trusted Publishing](https://rust-lang.github.io/rfcs/3691-trusted-publishing-cratesio.html)
- [Rust Blog: crates.io Trusted Publishing](https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07/)
- [GitHub: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub: OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)
- [GitHub: OIDC deployment hardening](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers)
- [GitHub: Deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [GitHub: Artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub: Immutable action releases and tags](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/using-immutable-releases-and-tags-to-manage-your-actions-releases)
