# Adding a detector

A detector is a single Python file in `scripts/detectors/`. The scanner loads
every `*.py` file in that directory when it starts. No registration and no
imports are needed.

## The file format

```python
"""Detector: <Provider> <credential type>.

VERIFY BEFORE RELYING ON THIS: confirm the current format against
<official documentation URL>.
"""

NAME = "provider-credential"     # lowercase, hyphenated, unique
SEVERITY = "high"                # critical, high, medium, or low
PATTERN = r"\bABC[0-9a-f]{32}\b"  # a raw-string regex matching the secret


def validate(value: str) -> bool:
    """Optional. Return False to discard a match."""
    return True
```

- `NAME` shows up in the report. Keep it short and stable.
- `SEVERITY` sets the sort order. Use `critical` for a secret that grants
  account access on its own, `high` for a scoped credential, `medium` for
  something that needs another value next to it, and `low` for indicators.
- `PATTERN` should match the secret itself. Variable names are already covered
  by the generic assignment detector built into `scan.py`.
- `validate` is optional. Use it for a checksum or a length check that a regex
  cannot express. The scanner ignores a broken `validate` instead of crashing.

Start from `detectors/template.py`, which is a copy-me file. Its pattern
matches a made-up marker and never fires on real code.

## Test your detector

1. Generate a fake value at runtime, for the format in the provider docs.
2. Add one case to `tests/run_tests.py` that scans a file containing the fake
   value and asserts the detector fires.
3. Add a case that the detector does not fire on a placeholder or on a nearby
   unrelated string.

Never commit a realistic-looking key, not even as a test string. Test fixtures
must build fake values in code, or GitHub push protection may flag the repo.

## Verify formats against the provider

Do not copy a key format from a blog post, a memory, or another scanner. Open
the provider's own documentation and confirm the prefix, length, and allowed
characters. Put that link in the module docstring so the next person can
recheck it.

Formats already shipped here carry a "VERIFY" note in their docstrings because
they were written from memory. Confirm them before relying on them.

### Formats used by the shipped detectors (verify these too)

These three patterns are already implemented, but they were written from memory
and must be checked against the provider's documentation before you trust them.
The exact strings the code currently uses:

- **AWS** - `\b(?:AKIA|ASIA)[0-9A-Z]{16}\b`. That is, the prefix `AKIA` or
  `ASIA` followed by 16 uppercase letters or digits, for a 20-character ID.
  Confirm the current prefixes and the length. Check the IAM access key ID
  reference in the AWS documentation.
- **GitHub** - classic tokens `gh[pousr]_` followed by 36 alphanumeric
  characters, and fine-grained tokens `github_pat_` followed by 22
  alphanumeric characters, an underscore, then 59 alphanumeric characters.
  Confirm every prefix and both lengths against GitHub's token format
  documentation.
- **Google** - `AIza` followed by 35 characters from `A-Za-z0-9_-`, for a
  39-character key. Confirm the prefix and length against Google Cloud's API
  key documentation.

### Formats that still need verification

These are not implemented yet. Treat every detail below as unverified. Check it
against the provider's own documentation before writing a detector, then put
the link in the detector docstring.

- **Stripe** - secret keys and restricted keys use a prefix, and test keys use
  a different one. Confirm the current prefixes, the length, and whether the
  separator is a hyphen or an underscore.
- **Paystack** - secret and public keys have different prefixes. Confirm both.
- **Flutterwave** - confirm the current key prefixes and lengths.
- **PEM private keys** - `-----BEGIN ... PRIVATE KEY-----` blocks. The skill
  description mentions private keys, but no detector covers them yet. Match the
  whole block, not just the header, and be careful about large files.
- **Other common providers not written yet** - Slack (`xox...`), Twilio, SendGrid
  (`SG.`), npm (`npm_`), and JWT-shaped values. Confirm each format, or decide
  that the generic assignment detector is good enough for that provider.

Because these were not verified, this project makes no claim about their
formats. Adding an unverified pattern risks missing real keys and flooding the
report with false positives.

## When a detector fires too much

Narrow the pattern, add a `validate` check, or add the noise to the project's
`.secret-scanner-allowlist`. Do not delete a useful detector just because one
file is noisy.

## Allowlist and inline ignores

- `.secret-scanner-allowlist` in the scanned project holds literal substrings
  matched against the path or the value, one per line, `#` for comments, and
  `re:` for a regular expression.
- An inline `secret-scanner:ignore` comment on a line (or the line above it)
  skips that line. Use it sparingly and leave a reason in the comment.
