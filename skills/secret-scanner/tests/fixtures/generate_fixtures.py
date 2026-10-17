"""Runtime fake-secret generators for the test suite.

Nothing in this file is a real credential, and no realistic-looking key is
ever written to disk in the repository. Every value is built from random
characters at run time, so GitHub push protection has nothing to flag.

The generators follow the same formats as the shipped detectors so the tests
exercise the detectors, but the formats themselves still need verification
against provider documentation (see references/adding-detectors.md).
"""

from __future__ import annotations

import random
import string
from pathlib import Path

UPPER_DIGITS = string.ascii_uppercase + string.digits
ALNUM = string.ascii_letters + string.digits
GOOGLE_ALPHABET = string.ascii_letters + string.digits + "_-"


def _pick(alphabet: str, length: int, rng: random.Random) -> str:
    return "".join(rng.choice(alphabet) for _ in range(length))


def fake_aws_access_key_id(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return "AKIA" + _pick(UPPER_DIGITS, 16, rng)


def fake_github_token(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return "ghp_" + _pick(ALNUM, 36, rng)


def fake_google_api_key(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return "AIza" + _pick(GOOGLE_ALPHABET, 35, rng)


def fake_high_entropy_value(rng: random.Random | None = None) -> str:
    """A random value that is not a known provider format, for the generic
    assignment detector."""
    rng = rng or random.Random()
    return _pick(ALNUM, 32, rng)


def _assignment(name: str, value: str, suffix: str = "") -> str:
    """Build a "name = value" line from pieces.

    The pieces are concatenated so this source file never contains a literal
    assignment that the scanner would flag when the skill scans itself.
    """
    return name + ' = "' + value + '"' + suffix + "\n"


def build_project(dest: Path, rng: random.Random | None = None) -> dict[str, str]:
    """Create a small fake project under *dest*.

    Returns the generated values so tests can assert that the raw secrets never
    appear in scanner output.
    """
    rng = rng or random.Random(2026)

    github_token = fake_github_token(rng)
    google_key = fake_google_api_key(rng)
    db_password = fake_high_entropy_value(rng)
    ignored_aws_key = fake_aws_access_key_id(rng)
    allowed_aws_key = fake_aws_access_key_id(rng)
    hidden_in_ignored_dir = fake_github_token(rng)
    hidden_in_binary = fake_google_api_key(rng)

    (dest / "src").mkdir(parents=True)
    (dest / "ignored_dir").mkdir(parents=True)

    (dest / ".gitignore").write_text("ignored_dir/\n", encoding="utf-8")

    (dest / "src" / "config.py").write_text(
        "# Example configuration for the tests.\n"
        + _assignment("GITHUB_TOKEN", github_token)
        + _assignment("GOOGLE_API_KEY", google_key),
        encoding="utf-8",
    )

    (dest / "src" / "settings.py").write_text(
        "# Generic assignment detector target.\n"
        + _assignment("DB_PASSWORD", db_password),
        encoding="utf-8",
    )

    (dest / "src" / "placeholders.py").write_text(
        "# These are obvious placeholders and must not be reported.\n"
        + _assignment("PASSWORD", "changeme")
        + _assignment("API_KEY", "your_api_key_here")
        + _assignment("TOKEN", "example")
        + _assignment("SIGNING_SECRET", "xxxxxxxx"),
        encoding="utf-8",
    )

    (dest / "src" / "ignored.py").write_text(
        "# The inline marker must suppress this finding.\n"
        + _assignment("AWS_ACCESS_KEY_ID", ignored_aws_key,
                      "  # secret-scanner:ignore"),
        encoding="utf-8",
    )

    (dest / "src" / "allowed.py").write_text(
        "# This value is listed in .secret-scanner-allowlist.\n"
        + _assignment("AWS_ACCESS_KEY_ID", allowed_aws_key),
        encoding="utf-8",
    )

    (dest / ".secret-scanner-allowlist").write_text(
        "# Test allowlist: literal substrings.\n" + allowed_aws_key + "\n",
        encoding="utf-8",
    )

    (dest / "ignored_dir" / "leaked.py").write_text(
        "# Covered by .gitignore, so it must be skipped.\n"
        + _assignment("GITHUB_TOKEN", hidden_in_ignored_dir),
        encoding="utf-8",
    )

    # Binary files are skipped even when they sit at a normal extension.
    (dest / "asset.txt").write_bytes(
        b"\x00\x01\x02 leaked: " + hidden_in_binary.encode("ascii") + b"\x00"
    )

    # Oversized file, skipped when --max-size is small.
    (dest / "oversized.py").write_text(
        _assignment("TOKEN", fake_high_entropy_value(rng)) + ("# pad\n" * 2000),
        encoding="utf-8",
    )

    return {
        "github_token": github_token,
        "google_key": google_key,
        "db_password": db_password,
        "ignored_aws_key": ignored_aws_key,
        "allowed_aws_key": allowed_aws_key,
        "hidden_in_ignored_dir": hidden_in_ignored_dir,
        "hidden_in_binary": hidden_in_binary,
    }
