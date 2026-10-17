#!/usr/bin/env python3
"""Tests for the secret-scanner skill.

Run from anywhere:

    python3 tests/run_tests.py

The tests build fake projects in a temporary directory. All secret-shaped
values are generated at run time, so no realistic key is committed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
SCAN = SKILL_DIR / "scripts" / "scan.py"
HAS_GIT = shutil.which("git") is not None

sys.path.insert(0, str(TESTS_DIR / "fixtures"))
import generate_fixtures as fixtures  # noqa: E402


def run_scan(root: Path, *args: str) -> tuple[int, str, str]:
    command = [sys.executable, str(SCAN), str(root), *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def scan_json(root: Path, *args: str) -> tuple[int, dict, str]:
    code, out, err = run_scan(root, "--json", *args)
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:  # pragma: no cover - test helper
        raise AssertionError(f"scanner did not return JSON: {out!r} ({exc})") from exc
    return code, data, err


def finding_paths(data: dict) -> set[str]:
    return {finding["file"] for finding in data["findings"]}


def run_git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=test@example.invalid",
         "-c", "user.name=Test", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")


class FixtureProjectTest(unittest.TestCase):
    """One generated project shared by the read-only assertions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name) / "project"
        cls.values = fixtures.build_project(cls.root)
        cls.code, cls.data, cls.stderr = scan_json(cls.root, "--max-size", "1000")
        cls.serialized = json.dumps(cls.data)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_detectors_load_without_warnings(self) -> None:
        self.assertNotIn("warning", self.stderr.lower())

    def test_finds_provider_and_generic_secrets(self) -> None:
        detectors = {finding["detector"] for finding in self.data["findings"]}
        self.assertIn("github-token", detectors)
        self.assertIn("google-api-key", detectors)
        self.assertIn("generic-assignment", detectors)
        self.assertGreater(self.data["total"], 0)

    def test_exit_code_is_one_when_findings_exist(self) -> None:
        self.assertEqual(self.code, 1)

    def test_raw_secrets_never_appear_in_output(self) -> None:
        for key in ("github_token", "google_key", "db_password",
                    "ignored_aws_key", "allowed_aws_key",
                    "hidden_in_ignored_dir", "hidden_in_binary"):
            self.assertNotIn(self.values[key], self.serialized, msg=key)

    def test_matches_are_redacted_to_four_characters(self) -> None:
        for finding in self.data["findings"]:
            redacted = finding["redacted"]
            self.assertTrue(redacted.endswith("******"))
            self.assertLessEqual(len(redacted) - 6, 4)

    def test_placeholders_are_not_reported(self) -> None:
        self.assertNotIn("src/placeholders.py", finding_paths(self.data))

    def test_inline_ignore_suppresses_a_finding(self) -> None:
        self.assertNotIn("src/ignored.py", finding_paths(self.data))

    def test_allowlist_suppresses_a_finding(self) -> None:
        self.assertNotIn("src/allowed.py", finding_paths(self.data))

    def test_gitignored_files_are_skipped(self) -> None:
        self.assertNotIn("ignored_dir/leaked.py", finding_paths(self.data))

    def test_binary_files_are_skipped(self) -> None:
        self.assertNotIn("asset.txt", finding_paths(self.data))

    def test_oversized_files_are_skipped(self) -> None:
        self.assertNotIn("oversized.py", finding_paths(self.data))

    def test_severity_counts_match_findings(self) -> None:
        total = sum(self.data["counts"].values())
        self.assertEqual(total, self.data["total"])


class CleanProjectTest(unittest.TestCase):
    def test_clean_project_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text(
                'PASSWORD = "changeme"\nAPI_KEY = "your_key_here"\n',
                encoding="utf-8",
            )
            code, data, _ = scan_json(root)
            self.assertEqual(code, 0)
            self.assertEqual(data["total"], 0)
            self.assertEqual(data["findings"], [])


class ErrorHandlingTest(unittest.TestCase):
    def test_missing_path_exits_two(self) -> None:
        code, _, err = run_scan(Path("/definitely/not/here/secret-scanner"))
        self.assertEqual(code, 2)
        self.assertIn("path not found", err)

    def test_help_text_is_available(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCAN), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--history", result.stdout)
        self.assertIn("--json", result.stdout)


@unittest.skipUnless(HAS_GIT, "git is required for this test")
class GitTest(unittest.TestCase):
    def test_hygiene_flags_a_tracked_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(root, "init", "-q")
            (root / ".env").write_text("APP_ENV=development\n", encoding="utf-8")
            run_git(root, "add", ".env")
            run_git(root, "commit", "-q", "-m", "add env")
            _, data, _ = scan_json(root)
            hygiene = [f for f in data["findings"] if f["detector"] == "hygiene"]
            self.assertTrue(hygiene)
            self.assertEqual(hygiene[0]["severity"], "critical")

    def test_history_finds_a_deleted_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(root, "init", "-q")
            secret = fixtures.fake_google_api_key()
            target = root / "config.py"
            target.write_text(f'GOOGLE_API_KEY = "{secret}"\n', encoding="utf-8")
            run_git(root, "add", "config.py")
            run_git(root, "commit", "-q", "-m", "add config")
            target.unlink()
            run_git(root, "commit", "-aq", "-m", "remove config")

            _, worktree, _ = scan_json(root)
            self.assertNotIn(
                "google-api-key", {f["detector"] for f in worktree["findings"]}
            )

            _, data, _ = scan_json(root, "--history")
            history_findings = [
                f for f in data["findings"]
                if f["source"] == "history" and f["detector"] == "google-api-key"
            ]
            self.assertTrue(history_findings)
            self.assertNotIn(secret, json.dumps(data))


if __name__ == "__main__":
    unittest.main(verbosity=2)
