"""Detector template. Copy this file, rename it, and edit the three values.

A detector is any Python file in the "detectors" directory that exposes the
attributes below. The scanner loads every *.py file in that directory.

    NAME      short, lowercase, hyphenated detector id shown in the report.
    SEVERITY  one of: critical, high, medium, low, info.
    PATTERN   a Python regular expression that matches the secret itself.
              Use a raw string (r"...") and word boundaries where possible.
    validate  OPTIONAL function taking the matched string and returning True
              to keep the finding or False to drop it. Use it for checksum or
              prefix checks that a regex cannot express.

Rules for a good detector:

1. Match the secret, not the variable name. The generic assignment detector
   in scan.py already covers "key = value" patterns.
2. Verify the format against the provider's official documentation and put
   the link in the module docstring. Never guess a format.
3. Prefer a narrow pattern. A detector that fires on everything trains the
   user to ignore the report.
4. Never put a real secret in a detector file or in its tests. Generate fake
   values at runtime (see tests/fixtures/generate_fixtures.py).

This template detector matches a made-up marker so it never fires on real
code. Replace PATTERN with your provider's format before enabling it.
"""

NAME = "template-example"
SEVERITY = "low"

# A deliberately fake marker. Replace this with a verified provider pattern.
PATTERN = r"\bTEMPLATE-DETECTOR-EXAMPLE-[0-9a-f]{8}\b"


def validate(value: str) -> bool:  # noqa: ARG001 - example signature
    """Optional hook. Return False to discard a match."""
    return True
