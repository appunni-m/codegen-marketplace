#!/usr/bin/env python3
"""Collect deterministic documentation evidence without claiming semantic quality."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

SCHEMA_VERSION = 1
MAX_TEXT_BYTES = 2_000_000

IGNORED_DIRECTORIES = {
    ".coverage-mcp",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
    "venv",
}

DOCUMENT_EXTENSIONS = {".adoc", ".markdown", ".md", ".mdx", ".rst"}

PROJECT_MARKERS = {
    "Cargo.toml": "Cargo/Rust",
    "CMakeLists.txt": "CMake",
    "DESCRIPTION": "R package",
    "Dockerfile": "Container",
    "Gemfile": "Ruby/Bundler",
    "Makefile": "Make",
    "Package.swift": "Swift Package Manager",
    "Project.toml": "Julia",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle/Kotlin",
    "composer.json": "Composer/PHP",
    "deno.json": "Deno",
    "deno.jsonc": "Deno",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "dune-project": "Dune/OCaml",
    "go.mod": "Go modules",
    "mix.exs": "Mix/Elixir",
    "package.json": "Node.js",
    "pom.xml": "Maven/Java",
    "pubspec.yaml": "Dart/Flutter",
    "pyproject.toml": "Python",
    "rebar.config": "Rebar/Erlang",
    "setup.cfg": "Python",
    "setup.py": "Python",
}

LANGUAGE_EXTENSIONS = {
    ".bash": "Shell",
    ".c": "C",
    ".cc": "C++",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".cxx": "C++",
    ".dart": "Dart",
    ".erl": "Erlang",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".f": "Fortran",
    ".f03": "Fortran",
    ".f08": "Fortran",
    ".f90": "Fortran",
    ".f95": "Fortran",
    ".for": "Fortran",
    ".fs": "F#",
    ".fsi": "F#",
    ".fsx": "F#",
    ".go": "Go",
    ".gql": "GraphQL",
    ".graphql": "GraphQL",
    ".h": "C/C++ header",
    ".hpp": "C++ header",
    ".hrl": "Erlang",
    ".hs": "Haskell",
    ".html": "HTML",
    ".java": "Java",
    ".jl": "Julia",
    ".js": "JavaScript",
    ".jsx": "JavaScript/JSX",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".lhs": "Literate Haskell",
    ".lua": "Lua",
    ".m": "Objective-C/MATLAB",
    ".mli": "OCaml",
    ".ml": "OCaml",
    ".mm": "Objective-C++",
    ".mjs": "JavaScript",
    ".nim": "Nim",
    ".php": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".proto": "Protocol Buffers",
    ".ps1": "PowerShell",
    ".py": "Python",
    ".r": "R",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sc": "Scala",
    ".sh": "Shell",
    ".sol": "Solidity",
    ".sql": "SQL",
    ".swift": "Swift",
    ".tf": "Terraform/HCL",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/TSX",
    ".zig": "Zig",
    ".zsh": "Shell",
}

ROOT_DOCUMENT_FAMILIES = {
    "readme": ("README",),
    "license": ("LICENSE", "LICENCE", "COPYING"),
    "contributing": ("CONTRIBUTING",),
    "security": ("SECURITY",),
    "code_of_conduct": ("CODE_OF_CONDUCT",),
    "support": ("SUPPORT",),
    "governance": ("GOVERNANCE",),
    "maintainers": ("MAINTAINERS",),
    "release": ("RELEASING", "RELEASE"),
    "changelog": ("CHANGELOG", "CHANGES", "NEWS"),
    "third_party_notices": ("THIRD_PARTY_NOTICES", "NOTICE"),
    "citation": ("CITATION",),
}

README_TOPIC_PATTERNS = {
    "status_or_compatibility": re.compile(
        r"\b(status|compatib(?:ility|le)?|support(?:ed)? versions?|requirements?|maturity)\b",
        re.IGNORECASE,
    ),
    "installation_or_quick_start": re.compile(
        r"\b(install(?:ation|ed|ing)?|setup|quick ?start|getting started)\b",
        re.IGNORECASE,
    ),
    "usage": re.compile(r"\b(usage|examples?|tutorial|how to)\b", re.IGNORECASE),
    "configuration": re.compile(
        r"\b(configur(?:ation|e|ed|ing)?|environment variables?|options?)\b",
        re.IGNORECASE,
    ),
    "reference": re.compile(r"\b(api|reference|commands?)\b", re.IGNORECASE),
    "troubleshooting_or_support": re.compile(
        r"\b(troubleshoot(?:ing)?|support|help|faq)\b", re.IGNORECASE
    ),
    "contributing": re.compile(
        r"\b(contribut(?:e|ing|ion|or|ors)?|development)\b", re.IGNORECASE
    ),
    "security": re.compile(r"\bsecurity\b", re.IGNORECASE),
    "license": re.compile(r"\blicen[cs]e\b", re.IGNORECASE),
}

REVIEW_CLAIMS = re.compile(
    r"\b("
    r"100%|all platforms|always secure|blazing fast|complete api|"
    r"fully documented|guaranteed|production[- ]ready|secure by default|"
    r"zero[- ]config(?:uration)?"
    r")\b",
    re.IGNORECASE,
)
PLACEHOLDERS = re.compile(r"\[(?:TODO|TBD)[^\]]*\]|\b(?:FIXME|TBD|TODO|XXX)\b")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
REFERENCE_LINK = re.compile(r"^[ \t]*\[[^\]]+\]:[ \t]*(\S+)", re.MULTILINE)
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})([^`]*)$")


def relative(path: Path, root: Path) -> str:
    """Return a stable POSIX-style path relative to the audited root."""
    return path.relative_to(root).as_posix()


def walk_files(root: Path) -> list[Path]:
    """Collect regular, non-symlink files while excluding generated dependency trees."""
    files: list[Path] = []
    for current, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if name not in IGNORED_DIRECTORIES
        )
        current_path = Path(current)
        for name in sorted(names):
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)
    return files


def read_text(path: Path) -> str | None:
    """Read bounded UTF-8 text, returning None for binary, oversized, or unreadable files."""
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def document_family(filename: str) -> str | None:
    """Classify a root filename into a conventional open-source document family."""
    uppercase = filename.upper()
    for family, prefixes in ROOT_DOCUMENT_FAMILIES.items():
        if any(uppercase == prefix or uppercase.startswith(prefix + ".") for prefix in prefixes):
            return family
    return None


def project_markers(root: Path, files: Iterable[Path]) -> list[dict[str, str]]:
    """Identify build and package markers without inferring unsupported capabilities."""
    markers: list[dict[str, str]] = []
    for path in files:
        rel = relative(path, root)
        name = path.name
        marker = PROJECT_MARKERS.get(name)
        if marker:
            markers.append({"path": rel, "kind": marker})
        elif path.suffix.lower() == ".csproj":
            markers.append({"path": rel, "kind": ".NET/C# project"})
        elif path.suffix.lower() == ".fsproj":
            markers.append({"path": rel, "kind": ".NET/F# project"})
        elif path.suffix.lower() == ".gemspec":
            markers.append({"path": rel, "kind": "Ruby gem"})
        elif path.suffix.lower() == ".cabal":
            markers.append({"path": rel, "kind": "Cabal/Haskell"})
        elif path.suffix.lower() == ".sln":
            markers.append({"path": rel, "kind": ".NET solution"})
        elif path.suffix.lower() == ".tf":
            markers.append({"path": rel, "kind": "Terraform"})
        elif name == "Chart.yaml":
            markers.append({"path": rel, "kind": "Helm"})
    return sorted(markers, key=lambda item: (item["path"], item["kind"]))


def language_counts(files: Iterable[Path]) -> list[dict[str, Any]]:
    """Count recognized source-language files in deterministic display order."""
    counts: Counter[str] = Counter()
    for path in files:
        language = LANGUAGE_EXTENSIONS.get(path.suffix.lower())
        if language:
            counts[language] += 1
        elif path.name == "Dockerfile" or path.name.startswith("Dockerfile."):
            counts["Dockerfile"] += 1
        elif path.name == "Makefile":
            counts["Make"] += 1
    return [
        {"language": language, "files": count}
        for language, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def root_documents(root: Path) -> dict[str, list[str]]:
    """Inventory conventional documentation files located at repository root."""
    found = {family: [] for family in ROOT_DOCUMENT_FAMILIES}
    try:
        entries = sorted(root.iterdir(), key=lambda path: path.name.lower())
    except OSError:
        return found
    for path in entries:
        if not path.is_file():
            continue
        family = document_family(path.name)
        if family:
            found[family].append(path.name)
    return found


def parse_link_target(raw: str) -> str:
    """Extract the destination component from a Markdown inline link target."""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def local_link_finding(
    source: Path,
    target: str,
    root: Path,
    line: int,
) -> dict[str, Any] | None:
    """Return a structural finding when a local link escapes the root or is missing."""
    lowered = target.lower()
    if (
        not target
        or target.startswith("#")
        or lowered.startswith(("data:", "http://", "https://", "mailto:", "tel:"))
    ):
        return None

    path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return None

    resolved = (source.parent / path_part).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return {
            "severity": "error",
            "code": "local_link_outside_repository",
            "path": relative(source, root),
            "line": line,
            "message": f"Local link escapes the repository: {target}",
        }
    if not resolved.exists():
        return {
            "severity": "error",
            "code": "broken_local_link",
            "path": relative(source, root),
            "line": line,
            "message": f"Missing local link target: {target}",
        }
    return None


def line_number(text: str, offset: int) -> int:
    """Translate a character offset into a one-based line number."""
    return text.count("\n", 0, offset) + 1


def inspect_markdown(path: Path, root: Path, text: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Inspect Markdown structure, local links, placeholders, and broad claims."""
    findings: list[dict[str, Any]] = []
    headings: list[dict[str, Any]] = []
    previous_level = 0
    fence_stack: list[tuple[str, int]] = []
    fence_count = 0
    unlabeled_fences = 0

    for index, content in enumerate(text.splitlines(), start=1):
        heading = HEADING.match(content)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            headings.append({"level": level, "title": title, "line": index})
            if previous_level and level > previous_level + 1:
                findings.append(
                    {
                        "severity": "review",
                        "code": "heading_level_jump",
                        "path": relative(path, root),
                        "line": index,
                        "message": f"Heading level jumps from {previous_level} to {level}: {title}",
                    }
                )
            previous_level = level

        fence = FENCE.match(content)
        if fence:
            marker = fence.group(1)
            if fence_stack and marker[0] == fence_stack[-1][0][0] and len(marker) >= len(
                fence_stack[-1][0]
            ):
                fence_stack.pop()
            else:
                fence_stack.append((marker, index))
                fence_count += 1
                if not fence.group(2).strip():
                    unlabeled_fences += 1

    for marker, index in fence_stack:
        findings.append(
            {
                "severity": "error",
                "code": "unbalanced_code_fence",
                "path": relative(path, root),
                "line": index,
                "message": f"Unclosed {marker[0] * len(marker)} code fence.",
            }
        )

    if unlabeled_fences:
        findings.append(
            {
                "severity": "review",
                "code": "unlabeled_code_fence",
                "path": relative(path, root),
                "line": None,
                "message": f"{unlabeled_fences} code fence(s) have no language label.",
            }
        )

    link_matches = list(INLINE_LINK.finditer(text)) + list(REFERENCE_LINK.finditer(text))
    for match in sorted(link_matches, key=lambda item: item.start()):
        target = parse_link_target(match.group(1))
        finding = local_link_finding(path, target, root, line_number(text, match.start()))
        if finding:
            findings.append(finding)

    for match in PLACEHOLDERS.finditer(text):
        findings.append(
            {
                "severity": "review",
                "code": "documentation_placeholder",
                "path": relative(path, root),
                "line": line_number(text, match.start()),
                "message": f"Review placeholder marker: {match.group(0)}",
            }
        )

    for match in REVIEW_CLAIMS.finditer(text):
        findings.append(
            {
                "severity": "review",
                "code": "broad_claim_requires_evidence",
                "path": relative(path, root),
                "line": line_number(text, match.start()),
                "message": f"Review evidence and scope for claim: {match.group(0)}",
            }
        )

    return (
        {
            "path": relative(path, root),
            "headings": headings,
            "code_fences": fence_count,
            "unlabeled_code_fences": unlabeled_fences,
        },
        findings,
    )


def inspect_repository(root: Path) -> dict[str, Any]:
    """Build the complete deterministic evidence report for one repository."""
    files = walk_files(root)
    documents = [
        path for path in files if path.suffix.lower() in DOCUMENT_EXTENSIONS
    ]
    root_docs = root_documents(root)
    findings: list[dict[str, Any]] = []
    markdown: list[dict[str, Any]] = []

    for path in documents:
        text = read_text(path)
        if text is None:
            findings.append(
                {
                    "severity": "info",
                    "code": "document_not_scanned",
                    "path": relative(path, root),
                    "line": None,
                    "message": f"Document was not UTF-8 text or exceeded {MAX_TEXT_BYTES} bytes.",
                }
            )
            continue
        details, document_findings = inspect_markdown(path, root, text)
        markdown.append(details)
        findings.extend(document_findings)

    for family, message in (
        ("readme", "No root README was found."),
        ("license", "No root license file was found; verify distribution terms."),
        ("contributing", "No root contribution guide was found."),
        ("security", "No root private security-reporting guide was found."),
    ):
        if not root_docs[family]:
            findings.append(
                {
                    "severity": "review",
                    "code": f"missing_{family}",
                    "path": ".",
                    "line": None,
                    "message": message,
                }
            )

    readme_details = next(
        (
            details
            for details in markdown
            if Path(details["path"]).parent == Path(".")
            and document_family(Path(details["path"]).name) == "readme"
        ),
        None,
    )
    readme_topics: list[str] = []
    if readme_details:
        heading_text = "\n".join(item["title"] for item in readme_details["headings"])
        readme_topics = [
            topic
            for topic, pattern in README_TOPIC_PATTERNS.items()
            if pattern.search(heading_text)
        ]

    severity_order = {"error": 0, "review": 1, "info": 2}
    findings.sort(
        key=lambda item: (
            severity_order[item["severity"]],
            item["path"],
            item["line"] if item["line"] is not None else 0,
            item["code"],
        )
    )
    counts = Counter(item["severity"] for item in findings)

    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(root),
        "inventory": {
            "project_markers": project_markers(root, files),
            "languages": language_counts(files),
            "root_documents": root_docs,
            "documentation_files": sorted(relative(path, root) for path in documents),
            "readme": readme_details,
            "readme_topics_observed": readme_topics,
        },
        "findings": findings,
        "summary": {
            "errors": counts["error"],
            "review": counts["review"],
            "info": counts["info"],
        },
        "limits": [
            "Presence, headings, and links do not prove that documentation is accurate or useful.",
            "External URL availability and whether a source supports a claim are not checked.",
            "Public API coverage, examples, generated docs, and distribution artifacts require native tooling.",
            "Review findings are prompts for human or agent judgment, not universal template failures.",
        ],
    }


def render_text(report: dict[str, Any]) -> str:
    """Render a compact human-readable form of the JSON-compatible report."""
    inventory = report["inventory"]
    lines = [
        "Documentation evidence inventory",
        f"Repository: {report['repository']}",
        "",
        "Project markers:",
    ]
    if inventory["project_markers"]:
        lines.extend(
            f"- {item['kind']}: {item['path']}" for item in inventory["project_markers"]
        )
    else:
        lines.append("- none observed")

    lines.extend(["", "Languages:"])
    if inventory["languages"]:
        lines.extend(
            f"- {item['language']}: {item['files']} file(s)"
            for item in inventory["languages"]
        )
    else:
        lines.append("- none observed")

    lines.extend(["", "Root documents:"])
    for family, paths in inventory["root_documents"].items():
        lines.append(f"- {family}: {', '.join(paths) if paths else 'not observed'}")

    lines.extend(["", "README topics observed:"])
    if inventory["readme_topics_observed"]:
        lines.extend(f"- {topic}" for topic in inventory["readme_topics_observed"])
    else:
        lines.append("- none observed")

    summary = report["summary"]
    lines.extend(
        [
            "",
            f"Findings: {summary['errors']} error(s), "
            f"{summary['review']} review item(s), {summary['info']} info item(s)",
        ]
    )
    for finding in report["findings"]:
        location = finding["path"]
        if finding["line"] is not None:
            location += f":{finding['line']}"
        lines.append(
            f"- [{finding['severity']}] {finding['code']} {location}: "
            f"{finding['message']}"
        )

    lines.extend(["", "Limits:"])
    lines.extend(f"- {limit}" for limit in report["limits"])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Inventory documentation evidence and structural review items."
    )
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return status 1 when structural error findings are present.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return 0, 1 for strict findings, or 2 for invalid input."""
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.repository).expanduser().resolve()
    if not root.is_dir():
        print(f"error: repository is not a directory: {root}", file=sys.stderr)
        return 2

    report = inspect_repository(root)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 1 if args.strict and report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
