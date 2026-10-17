"""Detector: GitHub tokens.

Covers classic personal access tokens, OAuth, user-to-server, server-to-server,
refresh tokens, and fine-grained personal access tokens.

VERIFY BEFORE RELYING ON THIS: confirm the prefixes and lengths against the
GitHub documentation on token formats:
https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github
This pattern was written from memory, not copied from the provider docs.
"""

NAME = "github-token"
SEVERITY = "critical"

# Classic prefixes: ghp_ (personal), gho_ (OAuth), ghu_ (user-to-server),
# ghs_ (server-to-server), ghr_ (refresh). Fine-grained: github_pat_.
PATTERN = r"\b(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59})\b"
