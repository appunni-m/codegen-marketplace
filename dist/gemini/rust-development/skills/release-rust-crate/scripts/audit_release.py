#!/usr/bin/env python3
"""Inventory structural Rust release risks without publishing or reading secrets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ACTION_RE = re.compile(
    r"^\s*-\s*uses:\s*['\"]?([^@\s'\"]+)@([^\s#'\"]+)", re.MULTILINE
)
FULL_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")
SEMVER_RE = re.compile(
    r"(?:0|[1-9][0-9]*)"
    r"\.(?:0|[1-9][0-9]*)"
    r"\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
TOKEN_LINE_RE = re.compile(r"^\s*CARGO_REGISTRY_TOKEN\s*:\s*(.+?)\s*$", re.MULTILINE)
PUBLISH_RE = re.compile(r"\bcargo\s+publish\b[^\r\n]*")
IGNORED_WORKFLOW_PREFIXES = ("./", "docker://")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically inventory Rust crate release evidence and workflow risks."
    )
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument(
        "--manifest-path",
        help="Cargo manifest path, relative to the repository unless absolute.",
    )
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="Audit only this publishable package; repeat for multiple packages.",
    )
    parser.add_argument("--registry", default="crates-io")
    parser.add_argument("--expected-version")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return one when structural error findings exist.",
    )
    return parser.parse_args()


def finding(
    severity: str,
    code: str,
    path: str,
    line: int,
    message: str,
) -> dict[str, object]:
    return {
        "severity": severity,
        "code": code,
        "path": path,
        "line": line,
        "message": message,
    }


def relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def git_inventory(
    root: Path, findings: list[dict[str, object]]
) -> dict[str, object]:
    inventory: dict[str, object] = {
        "repository": False,
        "head": None,
        "dirty_entries": None,
        "tags_at_head": [],
    }
    inside = run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        findings.append(
            finding(
                "review",
                "not_git_repository",
                ".",
                1,
                "The audit root is not a Git worktree; clean revision identity is not proven.",
            )
        )
        return inventory

    inventory["repository"] = True
    head = run(["git", "rev-parse", "HEAD"], root)
    if head.returncode == 0:
        inventory["head"] = head.stdout.strip()
    else:
        findings.append(
            finding(
                "error",
                "missing_head",
                ".git",
                1,
                "Git could not identify the release commit.",
            )
        )

    status = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if status.returncode == 0:
        entries = [line for line in status.stdout.splitlines() if line]
        inventory["dirty_entries"] = len(entries)
        if entries:
            findings.append(
                finding(
                    "error",
                    "dirty_worktree",
                    ".",
                    1,
                    f"The worktree has {len(entries)} changed or untracked entr{'y' if len(entries) == 1 else 'ies'}; do not publish with --allow-dirty.",
                )
            )
    else:
        findings.append(
            finding(
                "error",
                "git_status_failed",
                ".git",
                1,
                "Git could not prove that the release worktree is clean.",
            )
        )

    tags = run(["git", "tag", "--points-at", "HEAD"], root)
    if tags.returncode == 0:
        inventory["tags_at_head"] = sorted(filter(None, tags.stdout.splitlines()))

    tracked_credentials = run(
        ["git", "ls-files", ".cargo/credentials", ".cargo/credentials.toml"], root
    )
    if tracked_credentials.returncode == 0:
        for tracked in filter(None, tracked_credentials.stdout.splitlines()):
            findings.append(
                finding(
                    "error",
                    "tracked_cargo_credentials",
                    tracked,
                    1,
                    "A Cargo credentials file is tracked; remove and revoke exposed credentials without printing them.",
                )
            )
    return inventory


def load_metadata(
    root: Path,
    manifest: Path,
    findings: list[dict[str, object]],
) -> dict[str, Any] | None:
    command = [
        "cargo",
        "metadata",
        "--no-deps",
        "--format-version",
        "1",
        "--locked",
        "--manifest-path",
        str(manifest),
    ]
    result = run(command, root)
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        suffix = f" Last diagnostic: {detail[-1]}" if detail else ""
        findings.append(
            finding(
                "error",
                "cargo_metadata_failed",
                relative(root, manifest),
                1,
                "`cargo metadata --locked` failed; package identity and lock consistency are not proven."
                + suffix,
            )
        )
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        findings.append(
            finding(
                "error",
                "cargo_metadata_invalid",
                relative(root, manifest),
                1,
                f"Cargo returned invalid metadata JSON: {error}",
            )
        )
        return None


def supports_registry(package: dict[str, Any], registry: str) -> bool:
    publish = package.get("publish")
    return publish is None or registry in publish


def check_path_field(
    root: Path,
    package: dict[str, Any],
    key: str,
    findings: list[dict[str, object]],
) -> None:
    value = package.get(key)
    if not value:
        return
    path = Path(value)
    if not path.exists():
        manifest_path = Path(package["manifest_path"])
        findings.append(
            finding(
                "error",
                f"missing_{key}",
                relative(root, manifest_path),
                1,
                f"Package {package['name']} declares {key}={value}, but that file does not exist.",
            )
        )


def audit_packages(
    root: Path,
    metadata: dict[str, Any] | None,
    package_filters: list[str],
    registry: str,
    expected_version: str | None,
    findings: list[dict[str, object]],
) -> tuple[list[dict[str, object]], Path]:
    if metadata is None:
        return [], root

    workspace_root = Path(metadata["workspace_root"]).resolve()
    members = set(metadata.get("workspace_members", []))
    candidates = [
        package
        for package in metadata.get("packages", [])
        if package.get("id") in members and supports_registry(package, registry)
    ]
    by_name = {package["name"]: package for package in candidates}
    selected: list[dict[str, Any]] = []
    if package_filters:
        for name in package_filters:
            package = by_name.get(name)
            if package is None:
                findings.append(
                    finding(
                        "error",
                        "unknown_publish_package",
                        relative(root, Path(metadata["workspace_root"]) / "Cargo.toml"),
                        1,
                        f"Package {name} is not a publishable workspace member for registry {registry}.",
                    )
                )
            else:
                selected.append(package)
    else:
        selected = candidates

    if not selected:
        findings.append(
            finding(
                "error",
                "no_publishable_package",
                relative(root, Path(metadata["workspace_root"]) / "Cargo.toml"),
                1,
                f"No publishable workspace package was selected for registry {registry}.",
            )
        )
        return [], workspace_root

    package_inventory: list[dict[str, object]] = []
    for package in selected:
        manifest_path = Path(package["manifest_path"])
        version = str(package.get("version", ""))
        package_inventory.append(
            {
                "name": package["name"],
                "version": version,
                "manifest": relative(root, manifest_path),
                "rust_version": package.get("rust_version"),
                "target_kinds": sorted(
                    {
                        kind
                        for target in package.get("targets", [])
                        for kind in target.get("kind", [])
                    }
                ),
            }
        )

        if not SEMVER_RE.fullmatch(version):
            findings.append(
                finding(
                    "error",
                    "invalid_release_version",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} version {version!r} is not a complete SemVer release.",
                )
            )
        if expected_version and version != expected_version:
            findings.append(
                finding(
                    "error",
                    "version_mismatch",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} is {version}, expected {expected_version}.",
                )
            )
        if not package.get("description"):
            findings.append(
                finding(
                    "error",
                    "missing_description",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} has no registry description.",
                )
            )
        if not package.get("license") and not package.get("license_file"):
            findings.append(
                finding(
                    "error",
                    "missing_license",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} declares neither license nor license-file.",
                )
            )
        if not package.get("repository"):
            findings.append(
                finding(
                    "review",
                    "missing_repository",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} has no repository URL.",
                )
            )
        if not package.get("readme"):
            findings.append(
                finding(
                    "review",
                    "missing_readme",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} has no packaged README.",
                )
            )
        if not package.get("rust_version"):
            findings.append(
                finding(
                    "review",
                    "missing_rust_version",
                    relative(root, manifest_path),
                    1,
                    f"Package {package['name']} does not declare package.rust-version/MSRV.",
                )
            )
        check_path_field(root, package, "readme", findings)
        check_path_field(root, package, "license_file", findings)

    lockfile = workspace_root / "Cargo.lock"
    if not lockfile.exists():
        findings.append(
            finding(
                "error",
                "missing_lockfile",
                relative(root, workspace_root / "Cargo.toml"),
                1,
                "The workspace has no Cargo.lock; locked package/install evidence cannot be reproduced.",
            )
        )

    changelogs = [
        path
        for path in (
            workspace_root / "CHANGELOG.md",
            workspace_root / "CHANGES.md",
            root / "CHANGELOG.md",
        )
        if path.exists()
    ]
    changelogs = list(dict.fromkeys(path.resolve() for path in changelogs))
    for package in selected:
        version = str(package["version"])
        if not changelogs:
            findings.append(
                finding(
                    "review",
                    "missing_changelog",
                    relative(root, Path(package["manifest_path"])),
                    1,
                    f"No workspace changelog was found for package {package['name']} {version}.",
                )
            )
            continue
        if not any(
            re.search(rf"(?<![0-9A-Za-z]){re.escape(version)}(?![0-9A-Za-z])", path.read_text(encoding="utf-8", errors="replace"))
            for path in changelogs
        ):
            findings.append(
                finding(
                    "error",
                    "changelog_version_missing",
                    relative(root, changelogs[0]),
                    1,
                    f"No discovered changelog names release version {version} for package {package['name']}.",
                )
            )

    return package_inventory, workspace_root


def audit_workflow(
    root: Path,
    path: Path,
    findings: list[dict[str, object]],
) -> tuple[bool, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    relative_path = relative(root, path)
    action_count = 0
    for match in ACTION_RE.finditer(text):
        action, revision = match.groups()
        if action.startswith(IGNORED_WORKFLOW_PREFIXES):
            continue
        action_count += 1
        if not FULL_SHA_RE.fullmatch(revision):
            findings.append(
                finding(
                    "error",
                    "unpinned_action",
                    relative_path,
                    line_number(text, match.start()),
                    f"Action {action}@{revision} is movable; pin a reviewed full commit SHA.",
                )
            )

    publish_matches = list(PUBLISH_RE.finditer(text))
    if not publish_matches:
        return False, action_count

    if re.search(r"^\s*pull_request_target\s*:", text, re.MULTILINE):
        findings.append(
            finding(
                "error",
                "privileged_pull_request_target",
                relative_path,
                1,
                "A publishing workflow uses pull_request_target; do not execute untrusted PR code with release authority.",
            )
        )
    if "permissions:" not in text or "contents: read" not in text:
        findings.append(
            finding(
                "error",
                "release_permissions_not_minimal",
                relative_path,
                1,
                "The publishing workflow does not explicitly establish read-only contents permission.",
            )
        )
    if not re.search(r"\btags\s*:", text):
        findings.append(
            finding(
                "review",
                "release_not_tag_scoped",
                relative_path,
                1,
                "No tag filter was detected; verify the workflow has an intentional immutable release trigger.",
            )
        )
    if "timeout-minutes:" not in text:
        findings.append(
            finding(
                "review",
                "release_timeout_missing",
                relative_path,
                1,
                "No job timeout was detected; a lost runner may hold release concurrency indefinitely.",
            )
        )

    for match in publish_matches:
        command = match.group(0)
        command_line = line_number(text, match.start())
        if "--locked" not in command:
            findings.append(
                finding(
                    "error",
                    "publish_not_locked",
                    relative_path,
                    command_line,
                    "`cargo publish` does not use --locked.",
                )
            )
        if "--allow-dirty" in command:
            findings.append(
                finding(
                    "error",
                    "publish_allows_dirty",
                    relative_path,
                    command_line,
                    "`cargo publish --allow-dirty` breaks release/source identity.",
                )
            )
        if "--no-verify" in command:
            findings.append(
                finding(
                    "review",
                    "publish_skips_verification",
                    relative_path,
                    command_line,
                    "`cargo publish --no-verify` requires proof that an earlier required job verified the same archive/source.",
                )
            )

    uses_trusted_publishing = "rust-lang/crates-io-auth-action@" in text
    if uses_trusted_publishing:
        if "id-token: write" not in text:
            findings.append(
                finding(
                    "error",
                    "oidc_permission_missing",
                    relative_path,
                    1,
                    "The crates.io authentication action is present without id-token: write.",
                )
            )
        if not re.search(r"^\s*environment\s*:\s*\S+", text, re.MULTILINE):
            findings.append(
                finding(
                    "error",
                    "publish_environment_missing",
                    relative_path,
                    1,
                    "Trusted publication has no detected GitHub environment protection boundary.",
                )
            )

    token_matches = list(TOKEN_LINE_RE.finditer(text))
    if not token_matches:
        findings.append(
            finding(
                "error",
                "registry_token_binding_missing",
                relative_path,
                1,
                "The publishing workflow does not bind CARGO_REGISTRY_TOKEN for Cargo.",
            )
        )
    for match in token_matches:
        value = match.group(1)
        if "secrets." in value:
            findings.append(
                finding(
                    "error",
                    "long_lived_registry_secret",
                    relative_path,
                    line_number(text, match.start()),
                    "CARGO_REGISTRY_TOKEN comes from GitHub secrets; prefer crates.io Trusted Publishing.",
                )
            )
        elif "steps." not in value or ".outputs.token" not in value:
            findings.append(
                finding(
                    "error",
                    "untrusted_registry_token_source",
                    relative_path,
                    line_number(text, match.start()),
                    "CARGO_REGISTRY_TOKEN is not visibly sourced from a short-lived authentication step output.",
                )
            )

    if re.search(r"\bcargo\s+login\b", text):
        findings.append(
            finding(
                "error",
                "cargo_login_in_workflow",
                relative_path,
                1,
                "The release workflow invokes cargo login; do not persist long-lived registry credentials on runners.",
            )
        )
    if not ("GITHUB_REF_NAME" in text and "cargo metadata" in text):
        findings.append(
            finding(
                "review",
                "tag_version_check_missing",
                relative_path,
                1,
                "No direct tag-to-Cargo-metadata version assertion was detected.",
            )
        )
    return True, action_count


def workflow_inventory(
    root: Path, findings: list[dict[str, object]]
) -> dict[str, object]:
    workflow_root = root / ".github" / "workflows"
    paths = (
        sorted(
            path
            for path in workflow_root.iterdir()
            if path.is_file() and path.suffix in {".yml", ".yaml"}
        )
        if workflow_root.is_dir()
        else []
    )
    release_workflows: list[str] = []
    action_count = 0
    for path in paths:
        is_release, count = audit_workflow(root, path, findings)
        action_count += count
        if is_release:
            release_workflows.append(relative(root, path))
    if not release_workflows:
        findings.append(
            finding(
                "review",
                "automated_publish_missing",
                relative(root, workflow_root),
                1,
                "No GitHub workflow containing `cargo publish` was detected; verify the documented manual release path.",
            )
        )
    return {
        "files": [relative(root, path) for path in paths],
        "release_workflows": release_workflows,
        "external_action_uses": action_count,
    }


def render_text(report: dict[str, object]) -> str:
    inventory = report["inventory"]
    summary = report["summary"]
    lines = [
        "Rust release static evidence inventory",
        f"root: {inventory['root']}",
        f"head: {inventory['git']['head'] or 'not proven'}",
        f"publishable packages: {len(inventory['packages'])}",
        f"release workflows: {len(inventory['workflows']['release_workflows'])}",
        f"findings: {summary['errors']} error, {summary['review']} review, {summary['info']} info",
    ]
    for item in report["findings"]:
        lines.append(
            f"{str(item['severity']).upper()} {item['code']} "
            f"{item['path']}:{item['line']} {item['message']}"
        )
    lines.extend(
        [
            "",
            "This static inventory does not prove API compatibility, test correctness,",
            "credential safety outside the repository, package contents, or publication.",
            "Inspect findings, run the repository release gate, inspect the .crate, and",
            "verify the exact registry artifact from a clean consumer environment.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.repository).resolve()
    if not root.is_dir():
        print(f"error: repository directory does not exist: {root}", file=sys.stderr)
        return 2

    manifest = Path(args.manifest_path) if args.manifest_path else root / "Cargo.toml"
    if not manifest.is_absolute():
        manifest = root / manifest
    if not manifest.is_file():
        print(f"error: Cargo manifest does not exist: {manifest}", file=sys.stderr)
        return 2

    findings: list[dict[str, object]] = []
    git = git_inventory(root, findings)
    metadata = load_metadata(root, manifest, findings)
    packages, workspace_root = audit_packages(
        root,
        metadata,
        args.package,
        args.registry,
        args.expected_version,
        findings,
    )
    workflows = workflow_inventory(root, findings)
    findings.sort(
        key=lambda item: (
            {"error": 0, "review": 1, "info": 2}.get(str(item["severity"]), 3),
            str(item["path"]),
            int(item["line"]),
            str(item["code"]),
        )
    )
    counts = Counter(str(item["severity"]) for item in findings)
    report: dict[str, object] = {
        "schema_version": 1,
        "inventory": {
            "root": str(root),
            "manifest": relative(root, manifest),
            "workspace_root": relative(root, workspace_root),
            "registry": args.registry,
            "expected_version": args.expected_version,
            "git": git,
            "packages": packages,
            "workflows": workflows,
        },
        "findings": findings,
        "summary": {
            "errors": counts["error"],
            "review": counts["review"],
            "info": counts["info"],
        },
    }
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 1 if args.strict and counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
