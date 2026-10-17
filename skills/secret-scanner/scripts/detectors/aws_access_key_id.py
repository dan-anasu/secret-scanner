"""Detector: AWS access key IDs.

Matches access key IDs, not the secret access key that usually sits next to
them. The ID identifies an account and is still sensitive in a public repo.

VERIFY BEFORE RELYING ON THIS: confirm the current prefix and length against
the AWS documentation for IAM access key IDs:
https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
This pattern was written from memory, not copied from the provider docs.
"""

NAME = "aws-access-key-id"
SEVERITY = "high"

# AKIA = long-lived key, ASIA = temporary credentials from STS.
PATTERN = r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"
