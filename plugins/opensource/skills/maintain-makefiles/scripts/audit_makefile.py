#!/usr/bin/env python3
"""Statically inventory Makefiles without asking Make to parse them."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "node_modules",
    "target",
    "vendor",
}
MAKEFILE_NAMES = {"GNUmakefile", "Makefile", "makefile"}
ACTION_TARGETS = {
    "all",
    "build",
    "check",
    "clean",
    "dist",
    "distclean",
    "format",
    "generate",
    "help",
    "install",
    "installcheck",
    "lint",
    "package",
    "publish",
    "test",
    "uninstall",
    "update",
    "verify",
}
RULE_RE = re.compile(r"^([^#\s][^:=]*?):(?:([^=].*)?)$")
DEFAULT_GOAL_RE = re.compile(
    r"^\s*\.DEFAULT_GOAL\s*(?::=|::=|\?=|=)\s*([^\s#]+)"
)
PHONY_RE = re.compile(r"^\s*\.PHONY\s*:\s*(.*)$")
LITERAL_MAKE_RE = re.compile(r"^\s*[@+\-]?\s*make(?:\s|$)")
DESTRUCTIVE_RM_RE = re.compile(r"(?:^|[;&|]\s*)rm\s+[^#\n]*-[^\n#]*r[^\n#]*f")
VARIABLE_RE = re.compile(r"\$\([^)]+\)|\$\{[^}]+\}")
ASSIGNMENT_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\?=|:=|::=|\+=|!=|=)\s*(.*?)\s*$"
)
PLATFORM_VARIABLE_RE = re.compile(
    r"^(?:BUILD|HOST|TARGET)_(?:OS|ARCH|PLATFORM|VARIANT|TRIPLE)$"
)
TARGET_PLATFORM_VARIABLE_RE = re.compile(
    r"^TARGET_(?:OS|ARCH|PLATFORM|VARIANT|TRIPLE)$"
)
OUTPUT_DIRECTORY_RE = re.compile(
    r"^(?:BUILD|OUT|OUTPUT|BIN|DIST|ARTIFACT|PACKAGE)_DIR$"
)
UNAME_RE = re.compile(r"(?:\$\(\s*shell\s+[^)]*\buname\b|`[^`]*\buname\b)")
GNU_POSIX_MISMATCHES = (
    (re.compile(r"\$\((?:shell|wildcard|eval|file|call)\b"), "GNU function"),
    (re.compile(r"^\s*\.PHONY\s*:", re.MULTILINE), ".PHONY"),
    (re.compile(r"^\s*\.ONESHELL\s*:", re.MULTILINE), ".ONESHELL"),
    (re.compile(r"^\s*\.SECONDEXPANSION\s*:", re.MULTILINE), ".SECONDEXPANSION"),
    (re.compile(r"^[^#\n]+:\s*[^#\n]*\|", re.MULTILINE), "order-only prerequisite"),
    (re.compile(r"^\s*[A-Za-z0-9_.-]+\s*:=\s*", re.MULTILINE), ":= assignment"),
)


def makefiles_under(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRECTORIES for part in relative_parts[:-1]):
            continue
        if path.name in MAKEFILE_NAMES or path.suffix == ".mk":
            found.append(path)
    return sorted(found, key=lambda item: item.relative_to(root).as_posix())


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


def parse_rules(lines: list[str]) -> tuple[set[str], dict[str, list[tuple[int, str]]]]:
    targets: set[str] = set()
    recipes: dict[str, list[tuple[int, str]]] = {}
    current_targets: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("\t"):
            for target in current_targets:
                recipes.setdefault(target, []).append((line_number, line[1:]))
            continue
        current_targets = []
        match = RULE_RE.match(line)
        if not match:
            continue
        raw_targets = match.group(1).strip().split()
        for target in raw_targets:
            if (
                target.startswith(".")
                or "%" in target
                or "$" in target
                or "/" in target
            ):
                continue
            targets.add(target)
            current_targets.append(target)
    return targets, recipes


def clean_is_guarded(recipe: str) -> bool:
    has_nonempty_guard = bool(
        re.search(r"test\s+-n\s+['\"]?\$\([^)]+\)", recipe)
        or re.search(r"\[\s+-n\s+['\"]?\$\([^)]+\)", recipe)
    )
    has_root_guard = bool(
        re.search(r"(?:test|\[)[^\n;]*(?:!=|-ne)\s+['\"]?/['\"]?", recipe)
    )
    has_quoted_operand = bool(
        re.search(r"rm\s+[^#\n]*--\s+['\"]\$\([^)]+\)['\"]", recipe)
    )
    return has_nonempty_guard and has_root_guard and has_quoted_operand


def inspect_file(
    root: Path,
    path: Path,
) -> tuple[
    set[str],
    set[str],
    set[str],
    set[str],
    list[dict[str, object]],
    str | None,
]:
    relative = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    targets, recipes = parse_rules(lines)
    phony: set[str] = set()
    features: set[str] = set()
    platform_variables: set[str] = set()
    target_platform_variables: set[str] = set()
    output_directories: list[tuple[int, str, str]] = []
    findings: list[dict[str, object]] = []
    default_goal: str | None = None

    for line_number, line in enumerate(lines, start=1):
        assignment_match = ASSIGNMENT_RE.match(line)
        if assignment_match:
            variable_name, value = assignment_match.groups()
            if PLATFORM_VARIABLE_RE.match(variable_name):
                platform_variables.add(variable_name)
            if TARGET_PLATFORM_VARIABLE_RE.match(variable_name):
                target_platform_variables.add(variable_name)
                if UNAME_RE.search(value):
                    findings.append(
                        finding(
                            "review",
                            "host_derived_target",
                            relative,
                            line_number,
                            f"{variable_name} derives the target from build-system uname output.",
                        )
                    )
            if OUTPUT_DIRECTORY_RE.match(variable_name):
                output_directories.append((line_number, variable_name, value))

        if default_goal is None:
            goal_match = DEFAULT_GOAL_RE.match(line)
            if goal_match:
                default_goal = goal_match.group(1)

        phony_match = PHONY_RE.match(line)
        if phony_match:
            phony.update(phony_match.group(1).split())

        if "|" in line and RULE_RE.match(line) and not line.startswith("\t"):
            features.add("order_only_prerequisites")
        if ".ONESHELL:" in line:
            features.add("oneshell")
        if ".DELETE_ON_ERROR:" in line:
            features.add("delete_on_error")
        if ".SECONDEXPANSION:" in line:
            features.add("secondary_expansion")

        if not line.startswith("\t") and (
            "$(shell" in line or re.match(r"^\s*[^#:=]+\s*!=\s*", line)
        ):
            findings.append(
                finding(
                    "error",
                    "parse_time_shell",
                    relative,
                    line_number,
                    "Shell execution can occur while Make parses or expands this file.",
                )
            )

    if target_platform_variables:
        target_references = {
            f"$({name})" for name in target_platform_variables
        } | {
            f"${{{name}}}" for name in target_platform_variables
        }
        for line_number, variable_name, value in output_directories:
            if not any(reference in value for reference in target_references):
                findings.append(
                    finding(
                        "review",
                        "unscoped_platform_output",
                        relative,
                        line_number,
                        f"{variable_name} is shared across declared target-platform variants.",
                    )
                )

    if default_goal is None:
        for line in lines:
            match = RULE_RE.match(line)
            if not match:
                continue
            candidate = match.group(1).strip().split()[0]
            if not candidate.startswith(".") and "%" not in candidate and "$" not in candidate:
                default_goal = candidate
                break

    for target in sorted(targets & ACTION_TARGETS):
        if target not in phony:
            target_line = next(
                (
                    index
                    for index, line in enumerate(lines, start=1)
                    if re.match(rf"^{re.escape(target)}(?:\s|:)", line)
                ),
                1,
            )
            findings.append(
                finding(
                    "review",
                    "missing_phony",
                    relative,
                    target_line,
                    f"Action target '{target}' is not declared .PHONY.",
                )
            )

    for target, recipe_lines in sorted(recipes.items()):
        recipe = "\n".join(line for _, line in recipe_lines)
        for line_number, recipe_line in recipe_lines:
            if LITERAL_MAKE_RE.match(recipe_line):
                findings.append(
                    finding(
                        "error",
                        "literal_recursive_make",
                        relative,
                        line_number,
                        "Use $(MAKE) so recursive flags, overrides, and jobserver state propagate.",
                    )
                )
        if target in {"clean", "distclean", "maintainer-clean"}:
            for line_number, recipe_line in recipe_lines:
                if (
                    DESTRUCTIVE_RM_RE.search(recipe_line)
                    and VARIABLE_RE.search(recipe_line)
                    and not clean_is_guarded(recipe)
                ):
                    findings.append(
                        finding(
                            "error",
                            "unsafe_clean",
                            relative,
                            line_number,
                            "Recursive variable-based deletion lacks nonempty, root, and quoted-operand guards.",
                        )
                    )

    if re.search(r"^\s*\.POSIX\s*:", text, re.MULTILINE):
        for pattern, feature in GNU_POSIX_MISMATCHES:
            match = pattern.search(text)
            if match:
                line_number = text.count("\n", 0, match.start()) + 1
                findings.append(
                    finding(
                        "error",
                        "posix_dialect_mismatch",
                        relative,
                        line_number,
                        f"Claimed POSIX Makefile uses {feature}; verify or declare the required dialect.",
                    )
                )

    return (
        targets,
        phony,
        features,
        platform_variables,
        findings,
        default_goal,
    )


def build_report(root: Path, paths: list[Path]) -> dict[str, object]:
    targets: set[str] = set()
    phony: set[str] = set()
    features: set[str] = set()
    platform_variables: set[str] = set()
    findings: list[dict[str, object]] = []
    default_goal: str | None = None
    declared_dialect = "unspecified"

    for index, path in enumerate(paths):
        (
            file_targets,
            file_phony,
            file_features,
            file_platform_variables,
            file_findings,
            file_default,
        ) = inspect_file(root, path)
        targets.update(file_targets)
        phony.update(file_phony)
        features.update(file_features)
        platform_variables.update(file_platform_variables)
        findings.extend(file_findings)
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^\s*\.POSIX\s*:", text, re.MULTILINE):
            declared_dialect = "posix"
        if index == 0 and file_default:
            default_goal = file_default

    findings.sort(
        key=lambda item: (
            {"error": 0, "review": 1, "info": 2}[str(item["severity"])],
            str(item["path"]),
            int(item["line"]),
            str(item["code"]),
        )
    )
    counts = Counter(str(item["severity"]) for item in findings)
    return {
        "schema_version": 1,
        "root": str(root),
        "summary": {
            "errors": counts["error"],
            "review": counts["review"],
            "info": counts["info"],
        },
        "inventory": {
            "makefiles": [path.relative_to(root).as_posix() for path in paths],
            "declared_dialect": declared_dialect,
            "default_goal": default_goal,
            "targets": sorted(targets),
            "phony_targets": sorted(phony),
            "features": sorted(features),
            "platform_variables": sorted(platform_variables),
        },
        "findings": findings,
        "limits": [
            "Static evidence does not prove dependency or recipe correctness.",
            "Dynamic includes, generated syntax, and computed targets may be incomplete.",
            "Inspect findings before running make or a dry-run/database mode.",
        ],
    }


def print_text(report: dict[str, object]) -> None:
    summary = report["summary"]
    inventory = report["inventory"]
    assert isinstance(summary, dict)
    assert isinstance(inventory, dict)
    print("Makefile static evidence inventory")
    print(f"Makefiles: {len(inventory['makefiles'])}")
    print(f"Default goal: {inventory['default_goal'] or 'unknown'}")
    print(
        "Findings: "
        f"{summary['errors']} error(s), "
        f"{summary['review']} review item(s), "
        f"{summary['info']} info item(s)"
    )
    for item in report["findings"]:
        assert isinstance(item, dict)
        print(
            f"- {str(item['severity']).upper()} {item['code']} "
            f"{item['path']}:{item['line']} — {item['message']}"
        )
    print("Static evidence does not prove dependency or recipe correctness.")
    print("Inspect findings before running make, make -n, or make -qp.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Statically inventory Makefile evidence without invoking Make."
    )
    parser.add_argument("repository", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return 1 when error-severity findings are present.",
    )
    args = parser.parse_args()

    root = args.repository.resolve()
    if not root.is_dir():
        print("error: repository is not a directory", file=sys.stderr)
        return 2
    paths = makefiles_under(root)
    if not paths:
        print("error: no Makefile found", file=sys.stderr)
        return 2

    report = build_report(root, paths)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    summary = report["summary"]
    assert isinstance(summary, dict)
    return 1 if args.strict and int(summary["errors"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
