# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `secret-scanner` Agent Skill with `SKILL.md` following the Agent Skills
  specification.
- `scripts/scan.py`, a dependency-free Python 3 scanner that respects
  `.gitignore`, skips binaries and large files, redacts matches, supports an
  inline ignore marker and an allowlist file, scans git history with
  `--history`, checks `.env` hygiene, and returns a non-zero exit code on
  findings.
- A generic assignment detector with a Shannon entropy check.
- Starter detectors for AWS access key IDs, GitHub tokens, and Google API
  keys, plus a documented detector template.
- Tests that generate fake secrets at runtime, so no realistic key is
  committed.
- Reference docs for remediation and for adding detectors.
- Community and project health files adapted from
  `geekinks/open-source-project-template` (MIT).

### Notes

- The starter detector formats are written from memory and need verification
  against provider documentation before being relied on. See the README.

[Unreleased]: https://github.com/dan-anasu/secret-scanner/commits/main
