#!/usr/bin/env python3
"""scan.py - scan a local project for leaked secrets before publishing.

The scanner runs entirely on the local machine. It never opens a network
connection and never sends file contents or findings anywhere.

Usage:
    python3 scan.py [PATH] [options]

Common options:
    --history             also scan the git history (needs git)
    --json                print JSON instead of a markdown report
    --allowlist FILE      override the default .secret-scanner-allowlist
    --max-size BYTES      skip files larger than this (default 1048576)
    --quiet               only print the summary line
    --version, --help

Exit codes:
    0  no findings
    1  one or more findings
    2  usage or runtime error

Detectors live in the "detectors" directory next to this script. Each is a
small Python file exposing NAME, SEVERITY and PATTERN (and optionally a
validate function). See references/adding-detectors.md in the skill.
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

VERSION = "0.1.0"

DEFAULT_MAX_BYTES = 1_048_576  # 1 MiB
ENTROPY_THRESHOLD = 3.5
IGNORE_MARKER = "secret-scanner:ignore"
SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")
ALLOWLIST_FILENAME = ".secret-scanner-allowlist"

BINARY_EXTENSIONS = {
    ".7z", ".a", ".avi", ".bin", ".bmp", ".bz2", ".class", ".dat", ".db",
    ".dll", ".dylib", ".eot", ".exe", ".flac", ".gif", ".gz", ".heic",
    ".ico", ".idx", ".jar", ".jpeg", ".jpg", ".mkv", ".mov", ".mp3", ".mp4",
    ".o", ".ogg", ".otf", ".pack", ".pdf", ".png", ".psd", ".pyc", ".pyo",
    ".rar", ".so", ".sqlite", ".sqlite3", ".svgz", ".tar", ".tgz", ".tiff",
    ".ttf", ".war", ".wasm", ".wav", ".webp", ".woff", ".woff2", ".xz", ".zip",
}

DEFAULT_SKIP_DIRS = {
    ".cache", ".git", ".hg", ".idea", ".mypy_cache", ".next", ".nuxt",
    ".pytest_cache", ".ruff_cache", ".svn", ".terraform", ".venv", ".vscode",
    "__pycache__", "build", "coverage", "dist", "env", "node_modules",
    "target", "vendor", "venv",
}

# Values that are obviously not real secrets.
PLACEHOLDER_VALUES = {
    "123456", "1234567890", "abcdef", "abcdefgh", "apikey", "api-key",
    "api_key", "bar", "baz", "changeme", "change-me", "change_me", "default",
    "dummy", "example", "example_key", "fake", "foo", "insert_here", "nil",
    "none", "not_a_real_key", "notreal", "null", "passwd", "password",
    "placeholder", "pwd", "redacted", "removed", "replace_me", "sample",
    "secret", "test", "todo", "token", "xxx", "xxxx", "xxxxxx", "yourapikey",
    "your_api_key", "your-api-key",
}

PLACEHOLDER_SUBSTRINGS = (
    "${", "{{", "<", ">", "change-me", "change_me", "changeme", "example",
    "getenv", "insert_", "lorem", "notreal", "os.environ", "placeholder",
    "process.env", "redacted", "replace_me", "replaceme", "todo", "xxxx",
    "your-", "your_",
)

# Generic assignment detector. Matches "key = value" style lines whose name
# looks like a credential and whose value looks random enough to be real.
GENERIC_NAMES = (
    r"pass(?:word|wd|phrase)?", r"secret", r"token", r"api[-_]?key",
    r"apikey", r"access[-_]?key", r"secret[-_]?key", r"client[-_]?secret",
    r"auth(?:orization)?[-_]?token", r"private[-_]?key", r"credential",
)
# Note the lookbehind instead of \b: names are often prefixed with an
# underscore (DB_PASSWORD, GITHUB_TOKEN), and \b would not match after "_".
GENERIC_QUOTED = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:" + "|".join(GENERIC_NAMES) + r")\b\s*[:=]\s*"
    r"(?P<q>['\"])(?P<val>[^'\"\n]{8,})(?P=q)"
)
GENERIC_BARE = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:" + "|".join(GENERIC_NAMES) + r")\b\s*[:=]\s*"
    r"(?P<val>[A-Za-z0-9_+/=\-]{16,})"
)


class ScanError(Exception):
    """A user-facing problem that should end the run with exit code 2."""


@dataclass
class Detector:
    name: str
    severity: str
    pattern: re.Pattern
    validate: object = None
    source: str = ""


@dataclass
class Finding:
    path: str
    line: int
    detector: str
    severity: str
    value: str
    verdict: str
    source: str = "worktree"
    commit: str = ""

    def to_dict(self) -> dict:
        # The raw value is deliberately not exposed. Only a redacted form is
        # ever written to the report.
        return {
            "file": self.path,
            "line": self.line,
            "detector": self.detector,
            "severity": self.severity,
            "redacted": redact(self.value),
            "verdict": self.verdict,
            "source": self.source,
            "commit": self.commit,
        }


def shannon_entropy(value: str) -> float:
    """Return the Shannon entropy of a string in bits per character."""
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    return -sum(
        (count / length) * math.log2(count / length) for count in counts.values()
    )


def redact(value: str) -> str:
    """Show only the first four characters, padded with a fixed width mask.

    The mask width is constant so the report does not leak the length of the
    original value.
    """
    if not value:
        return "(empty)"
    head = value[:4] if len(value) > 4 else value[:1]
    return head + "*" * 6


def looks_like_placeholder(value: str) -> bool:
    text = value.strip().strip("\"'").strip()
    if not text:
        return True
    lowered = text.lower()
    if lowered in PLACEHOLDER_VALUES:
        return True
    if any(token in lowered for token in PLACEHOLDER_SUBSTRINGS):
        return True
    if len(set(text)) <= 2:  # e.g. "aaaa", "000000"
        return True
    return False


def classify(value: str, entropy_floor: float = 0.0) -> str:
    """Give a first-pass verdict that a human can override during triage."""
    if looks_like_placeholder(value):
        return "likely placeholder"
    if shannon_entropy(value) < max(3.0, entropy_floor):
        return "likely placeholder"
    return "needs review"


def load_detectors(detectors_dir: Path) -> list[Detector]:
    detectors: list[Detector] = []
    if not detectors_dir.is_dir():
        print(
            f"warning: no detector directory at {detectors_dir}, "
            "continuing with the generic detector only",
            file=sys.stderr,
        )
        return detectors
    for path in sorted(detectors_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = f"scan_detector_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            print(f"warning: could not load {path.name}", file=sys.stderr)
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"warning: detector {path.name} failed to load: {exc}", file=sys.stderr)
            continue
        missing = [key for key in ("NAME", "SEVERITY", "PATTERN") if not hasattr(module, key)]
        if missing:
            print(
                f"warning: skipping {path.name}: missing {', '.join(missing)}",
                file=sys.stderr,
            )
            continue
        try:
            pattern = re.compile(module.PATTERN)
        except re.error as exc:
            print(f"warning: skipping {path.name}: invalid PATTERN ({exc})", file=sys.stderr)
            continue
        detectors.append(
            Detector(
                name=str(module.NAME),
                severity=str(module.SEVERITY).lower(),
                pattern=pattern,
                validate=getattr(module, "validate", None),
                source=path.name,
            )
        )
    return detectors


def severity_rank(severity: str) -> int:
    try:
        return SEVERITY_ORDER.index(severity)
    except ValueError:
        return len(SEVERITY_ORDER)


class Allowlist:
    """Line-based allowlist. Blank lines and # comments are ignored.

    A line matches if it is a literal substring of the file path or of the
    matched value. Prefix a line with "re:" for a regular expression.
    """

    def __init__(self, rules: list[str]):
        self.literals: list[str] = []
        self.regexes: list[re.Pattern[str]] = []
        for rule in rules:
            rule = rule.strip()
            if not rule or rule.startswith("#"):
                continue
            if rule.startswith("re:"):
                try:
                    self.regexes.append(re.compile(rule[3:]))
                except re.error as exc:
                    print(f"warning: bad allowlist regex {rule!r}: {exc}", file=sys.stderr)
            else:
                self.literals.append(rule)

    @classmethod
    def load(cls, path: Path) -> "Allowlist":
        if not path.is_file():
            return cls([])
        try:
            return cls(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError as exc:
            print(f"warning: could not read allowlist {path}: {exc}", file=sys.stderr)
            return cls([])

    def allows(self, relative_path: str, value: str) -> bool:
        haystacks = (relative_path, value)
        for literal in self.literals:
            if any(literal in hay for hay in haystacks):
                return True
        for regex in self.regexes:
            if any(regex.search(hay) for hay in haystacks):
                return True
        return False


class GitignoreMatcher:
    """A small subset of gitignore rules, enough for a pre-push scan.

    Supports comments, blank lines, negation with "!", directory-only rules
    ending in "/", anchored rules starting with "/", and "*"/"?"/"**" globs.
    """

    def __init__(self, root: Path):
        self.root = root
        self.rules: list[tuple[Path, str, bool, bool]] = []  # base, pattern, negated, dir_only

    def add_file(self, gitignore_path: Path) -> None:
        base = gitignore_path.parent
        try:
            content = gitignore_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        for raw in content.splitlines():
            line = raw.rstrip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            if negated:
                line = line[1:]
            dir_only = line.endswith("/")
            line = line.rstrip("/")
            if not line:
                continue
            if line.startswith("/"):
                line = line[1:]
            self.rules.append((base, line, negated, dir_only))

    def is_ignored(self, path: Path, is_dir: bool) -> bool:
        ignored = False
        for base, pattern, negated, dir_only in self.rules:
            if dir_only and not is_dir:
                continue
            try:
                rel = path.relative_to(base).as_posix()
            except ValueError:
                continue
            if self._matches(rel, path.name, pattern):
                ignored = not negated
        return ignored

    @staticmethod
    def _matches(rel: str, name: str, pattern: str) -> bool:
        if "/" in pattern:
            if fnmatch.fnmatch(rel, pattern):
                return True
            return fnmatch.fnmatch(rel, pattern + "/**")
        if fnmatch.fnmatch(name, pattern):
            return True
        return any(fnmatch.fnmatch(part, pattern) for part in rel.split("/"))


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(8192)
    except OSError:
        return True
    if b"\x00" in chunk:
        return True
    return False


def iter_files(root: Path, matcher: GitignoreMatcher, max_bytes: int):
    """Yield candidate files, honouring .gitignore and skipping junk."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        current = Path(dirpath)
        gitignore = current / ".gitignore"
        if gitignore.is_file():
            matcher.add_file(gitignore)

        kept: list[str] = []
        for name in sorted(dirnames):
            child = current / name
            if name in DEFAULT_SKIP_DIRS:
                continue
            if matcher.is_ignored(child, is_dir=True):
                continue
            kept.append(name)
        dirnames[:] = kept

        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or not path.is_file():
                continue
            if path.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if matcher.is_ignored(path, is_dir=False):
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            if is_binary(path):
                continue
            yield path


def is_ignored_line(lines: list[str], index: int) -> bool:
    """index is 1-based. Honour a marker on the same or previous line."""
    if IGNORE_MARKER in lines[index - 1]:
        return True
    if index >= 2 and IGNORE_MARKER in lines[index - 2]:
        return True
    return False


def tidy_detector(finding_key: tuple, seen: set) -> bool:
    if finding_key in seen:
        return False
    seen.add(finding_key)
    return True


def scan_text(
    text: str,
    relative_path: str,
    detectors: list[Detector],
    allowlist: Allowlist,
    source: str = "worktree",
    commit: str = "",
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple] = set()
    lines = text.splitlines()

    for number, line in enumerate(lines, start=1):
        if is_ignored_line(lines, number):
            continue
        for detector in detectors:
            for match in detector.pattern.finditer(line):
                value = match.group(0)
                if detector.validate is not None:
                    try:
                        if not detector.validate(value):
                            continue
                    except Exception:  # noqa: BLE001 - a broken hook must not crash the scan
                        continue
                if allowlist.allows(relative_path, value):
                    continue
                key = (relative_path, number, detector.name, value, source, commit)
                if not tidy_detector(key, seen):
                    continue
                findings.append(
                    Finding(
                        path=relative_path,
                        line=number,
                        detector=detector.name,
                        severity=detector.severity,
                        value=value,
                        verdict=classify(value),
                        source=source,
                        commit=commit,
                    )
                )

        for match in GENERIC_QUOTED.finditer(line):
            value = match.group("val")
            if allowlist.allows(relative_path, value):
                continue
            if looks_like_placeholder(value) or shannon_entropy(value) < ENTROPY_THRESHOLD:
                continue
            key = (relative_path, number, "generic-assignment", value, source, commit)
            if not tidy_detector(key, seen):
                continue
            findings.append(
                Finding(
                    path=relative_path,
                    line=number,
                    detector="generic-assignment",
                    severity="medium",
                    value=value,
                    verdict="needs review",
                    source=source,
                    commit=commit,
                )
            )

        for match in GENERIC_BARE.finditer(line):
            value = match.group("val")
            if allowlist.allows(relative_path, value):
                continue
            if looks_like_placeholder(value):
                continue
            if shannon_entropy(value) < ENTROPY_THRESHOLD + 0.5:
                continue
            key = (relative_path, number, "generic-assignment", value, source, commit)
            if not tidy_detector(key, seen):
                continue
            findings.append(
                Finding(
                    path=relative_path,
                    line=number,
                    detector="generic-assignment",
                    severity="medium",
                    value=value,
                    verdict="needs review",
                    source=source,
                    commit=commit,
                )
            )
    return findings


def scan_worktree(root: Path, detectors: list[Detector], allowlist: Allowlist, max_bytes: int):
    findings: list[Finding] = []
    scanned = 0
    matcher = GitignoreMatcher(root)
    for path in iter_files(root, matcher, max_bytes):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned += 1
        relative = path.relative_to(root).as_posix()
        findings.extend(scan_text(text, relative, detectors, allowlist))
    return findings, scanned


def run_git(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ScanError("git was not found on PATH but --history was requested") from exc
    if result.returncode != 0:
        raise ScanError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def is_git_repo(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def scan_history(root: Path, detectors: list[Detector], allowlist: Allowlist) -> list[Finding]:
    """Scan added lines in every commit. Line numbers come from hunk headers."""
    output = run_git(root, ["log", "-p", "--all", "--no-color", "--unified=0"])
    findings: list[Finding] = []
    current_file = ""
    commit = ""
    target_line = 0
    for raw in output.splitlines():
        if raw.startswith("commit "):
            commit = raw.split()[1][:8]
            continue
        if raw.startswith("+++ "):
            current_file = raw[6:].strip()
            if current_file.startswith("b/"):
                current_file = current_file[2:]
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            target_line = int(match.group(1)) if match else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            content = raw[1:]
            findings.extend(
                scan_text(
                    content,
                    current_file or "(unknown)",
                    detectors,
                    allowlist,
                    source="history",
                    commit=commit,
                )
            )
            target_line += 1
        elif raw.startswith("-") or raw.startswith("diff --git") or raw.startswith("---"):
            continue
        else:
            continue
    return findings


def check_hygiene(root: Path) -> list[Finding]:
    """Check whether .env is ignored, and whether it is tracked by git."""
    findings: list[Finding] = []
    env_file = root / ".env"
    if not env_file.exists():
        return findings

    repo = is_git_repo(root)
    matcher = GitignoreMatcher(root)
    for candidate in root.rglob(".gitignore"):
        matcher.add_file(candidate)
    ignored = matcher.is_ignored(env_file, is_dir=False)

    tracked = False
    if repo:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", ".env"],
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = result.returncode == 0

    if tracked:
        findings.append(
            Finding(
                path=".env",
                line=0,
                detector="hygiene",
                severity="critical",
                value=".env is tracked by git",
                verdict="needs review",
            )
        )
    elif not ignored:
        findings.append(
            Finding(
                path=".env",
                line=0,
                detector="hygiene",
                severity="medium",
                value=".env exists and is not ignored",
                verdict="needs review",
            )
        )
    return findings


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda item: (
            severity_rank(item.severity),
            item.path,
            item.line,
            item.detector,
        ),
    )


def count_by_severity(findings: list[Finding]) -> dict[str, int]:
    counts = {level: 0 for level in SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def render_summary(counts: dict[str, int], total: int, scanned: int) -> str:
    parts = [f"{counts.get(level, 0)} {level}" for level in SEVERITY_ORDER]
    return (
        f"Summary: {total} finding(s) "
        f"({', '.join(parts)}) across {scanned} file(s) scanned"
    )


REMEDIATION_CHECKLIST = [
    "Rotate or revoke every credential confirmed as real. Do this first: "
    "deleting the file does not invalidate a leaked secret.",
    "Move the value into an environment variable or a secrets manager and "
    "load it at runtime.",
    "If the secret was ever committed, clean the git history (git filter-repo "
    "or BFG) and force-push, then tell collaborators to re-clone.",
    "Add prevention: ignore the file in .gitignore and add a pre-commit hook "
    "or CI check that runs this scanner.",
]


def render_report(
    findings: list[Finding], counts: dict[str, int], total: int, scanned: int, root: Path
) -> str:
    lines = ["# secret-scanner report", ""]
    lines.append(render_summary(counts, total, scanned))
    lines.append(f"Root: {root}")
    lines.append("")
    if not findings:
        lines.append("No findings. This does not prove the project is safe; "
                     "no scanner catches every secret.")
        return "\n".join(lines) + "\n"

    lines.append("## Findings")
    lines.append("")
    lines.append("| File | Line | Detector | Severity | Redacted match | Verdict |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for finding in findings:
        location = finding.path + (f" @ {finding.commit}" if finding.commit else "")
        lines.append(
            f"| {location} | {finding.line} | {finding.detector} | "
            f"{finding.severity} | `{redact(finding.value)}` | {finding.verdict} |"
        )
    lines.append("")
    lines.append("## Remediation checklist")
    lines.append("")
    for step in REMEDIATION_CHECKLIST:
        lines.append(f"- [ ] {step}")
    lines.append("")
    lines.append(
        "A clean scan is not proof of safety. No scanner catches every secret."
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description=(
            "Scan a local project for leaked secrets. Runs offline and only "
            "ever prints redacted matches."
        ),
        epilog="Exit codes: 0 clean, 1 findings, 2 error.",
    )
    parser.add_argument("path", nargs="?", default=".", help="project directory to scan")
    parser.add_argument("--version", action="version", version=f"secret-scanner {VERSION}")
    parser.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    parser.add_argument("--history", action="store_true", help="also scan git history (needs git)")
    parser.add_argument("--allowlist", metavar="FILE", help="path to an allowlist file")
    parser.add_argument(
        "--max-size",
        type=int,
        default=DEFAULT_MAX_BYTES,
        metavar="BYTES",
        help=f"skip files larger than this (default {DEFAULT_MAX_BYTES})",
    )
    parser.add_argument("--quiet", action="store_true", help="print only the summary line")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_size < 0:
        print("error: --max-size must be zero or greater", file=sys.stderr)
        return 2

    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    detectors = load_detectors(Path(__file__).resolve().parent / "detectors")
    allowlist_path = (
        Path(args.allowlist).expanduser().resolve()
        if args.allowlist
        else root / ALLOWLIST_FILENAME
    )
    allowlist = Allowlist.load(allowlist_path)

    try:
        findings, scanned = scan_worktree(root, detectors, allowlist, args.max_size)
        findings.extend(check_hygiene(root))
        if args.history:
            if not is_git_repo(root):
                print("warning: --history was set but this is not a git repository",
                      file=sys.stderr)
            else:
                history_findings = scan_history(root, detectors, allowlist)
                findings.extend(history_findings)
    except ScanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings = sort_findings(findings)
    counts = count_by_severity(findings)
    total = len(findings)

    if args.json:
        payload = {
            "version": VERSION,
            "root": str(root),
            "files_scanned": scanned,
            "counts": counts,
            "total": total,
            "findings": [finding.to_dict() for finding in findings],
            "remediation": REMEDIATION_CHECKLIST,
            "notice": "A clean scan is not proof of safety; no scanner catches every secret.",
        }
        print(json.dumps(payload, indent=2))
    elif args.quiet:
        print(render_summary(counts, total, scanned))
    else:
        print(render_report(findings, counts, total, scanned, root), end="")

    return 1 if total else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(130)
