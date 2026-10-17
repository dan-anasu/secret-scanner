"""Detector: Google API keys.

Matches the common "AIza..." API key format used by Google Cloud and Maps
APIs. Service account JSON files and OAuth client secrets use other formats
and are not covered here.

VERIFY BEFORE RELYING ON THIS: confirm the current prefix and length against
the Google Cloud API key documentation:
https://cloud.google.com/docs/authentication/api-keys
This pattern was written from memory, not copied from the provider docs.
"""

NAME = "google-api-key"
SEVERITY = "high"

PATTERN = r"\bAIza[0-9A-Za-z_\-]{35}\b"
