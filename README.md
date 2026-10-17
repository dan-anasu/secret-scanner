# secret-scanner

> A local, offline secret scanner packaged as an Agent Skill. Point it at a
> project before you push, triage the findings, and fix them in the right order.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md) [![Hacktoberfest friendly](https://img.shields.io/badge/Hacktoberfest-friendly-orange.svg)](CONTRIBUTING.md)

`secret-scanner` helps developers, students, and hobbyists check a project for
leaked passwords, API keys, tokens, and private keys **before** they push it to
a public or shared repository.

**Status:** early. The scanner works and is tested. The key formats in the
starter detectors still need verification against provider documentation. See
[Verification needed](#verification-needed).

## Why this project exists

**Problem:** it is easy to commit a `.env` file, paste an API key into a
config file, or forget a token in a script. Once the commit is public, the
credential is effectively invalid and often still sitting in the git history.

**Intended users:** developers, students, and hobbyists about to push code to a
public or shared repository.

**Approach:** a dependency-free Python 3 script walks the project, respects
`.gitignore`, skips binaries and large files, and runs a set of small detectors
plus a generic high-entropy assignment check. An agent (or you) then triages
each finding as a real secret or a likely placeholder and fixes the real ones.
**Limitation:** no scanner catches every secret. A clean report lowers risk; it
does not prove the project is safe.

## Features

- **Offline by design.** The scanner never opens a network connection and never
  sends file contents or findings anywhere.
- **Redaction by default.** Every reported match is shown as the first four
  characters plus asterisks, never in full.
- **Respects `.gitignore`,** skips binary files and files over a size limit.
- **Pluggable detectors.** One small file per provider; the scanner loads every
  file in `scripts/detectors/` automatically.
- **Generic detection.** A fallback detector finds `password = "..."` style
  assignments and filters weak values with a Shannon entropy check.
- **Placeholder aware.** Common example and test values are labelled, not
  silently dropped.
- **Inline ignores and an allowlist** for the false positives you accept.
- **History scan.** `--history` looks for secrets that were deleted but remain
  in old commits.
- **Hygiene check.** Flags a tracked `.env` or an unignored `.env`.
- **Text or `--json` output,** and a non-zero exit code when anything is found,
  so it drops straight into a pre-commit hook or CI step.

## The Agent Skill

The skill lives in [`skills/secret-scanner/`](skills/secret-scanner/). It
follows the [Agent Skills Open Standard](https://agentskills.io/) (the
`SKILL.md` frontmatter and directory layout described at
[agentskills.io/specification](https://agentskills.io/specification)).

An agent that supports skills loads `SKILL.md` and then:

1. asks for the project path, whether to scan git history, and whether the
   repository is already public,
2. runs the bundled scanner,
3. triages each finding as a real secret or a likely placeholder,
4. walks the user through rotation, storage, history cleanup, and prevention.

The original behavior this project contributes is the combination of a
zero-dependency scanner, per-provider plug-in detectors, placeholder triage,
and remediation ordering, shipped as a portable skill. The skill's own
instructions live only in `SKILL.md`; the scanner does the work locally.

## Prerequisites and installation

**Prerequisites:** Python 3.9 or newer. `git` is optional, only for
`--history` and for the tracked-`.env` hygiene check. No third-party packages.

```sh
git clone https://github.com/dan-anasu/secret-scanner.git
cd secret-scanner
```

There is nothing to install. The scanner is a single file.

## Usage

Scan a project:

```sh
python3 skills/secret-scanner/scripts/scan.py /path/to/project
```

Include the git history and machine-readable output:

```sh
python3 skills/secret-scanner/scripts/scan.py . --history
python3 skills/secret-scanner/scripts/scan.py . --json
```

Example output (values are fake):

```
Summary: 5 finding(s) (1 critical, 1 high, 3 medium, 0 low, 0 info) across 7 file(s) scanned

| File | Line | Detector | Severity | Redacted match | Verdict |
| --- | --- | --- | --- | --- | --- |
| src/config.py | 2 | github-token | critical | `ghp_******` | needs review |
| src/config.py | 3 | google-api-key | high | `AIza******` | needs review |
```

Options:

| Flag | Meaning |
| --- | --- |
| `--history` | also scan added lines in every commit (needs `git`) |
| `--json` | print JSON instead of a Markdown report |
| `--allowlist FILE` | use a specific allowlist file |
| `--max-size BYTES` | skip files larger than this (default 1048576) |
| `--quiet` | print only the summary line |
| `--version`, `--help` | version and usage |

Exit codes: `0` no findings, `1` findings, `2` usage or runtime error.

## How detection works

- **Detectors** in `scripts/detectors/` each expose `NAME`, `SEVERITY`,
  `PATTERN`, and an optional `validate`. See
  [`references/adding-detectors.md`](skills/secret-scanner/references/adding-detectors.md).
- **Generic assignment detector** matches credential-like names and keeps only
  values above an entropy threshold, so `password = "hunter2"` is not shouted
  about but `password = "9f2K..."` is.
- **Placeholder filter** recognises common example values (`changeme`,
  `your_api_key_here`, `xxxxxxxx`, template markers, and similar).
- **Redaction** shows the first four characters plus a fixed-width mask, so the
  original length is not leaked either.
- **Inline ignore:** add `secret-scanner:ignore` to a line (or the line above
  it) to suppress findings on it.
- **Allowlist:** put literal substrings (or `re:` regular expressions) in
  `.secret-scanner-allowlist` at the project root.

Shipped detectors:

| Detector | Severity | Matches |
| --- | --- | --- |
| `aws-access-key-id` | high | AWS access key IDs (`AKIA...`, `ASIA...`) |
| `github-token` | critical | GitHub classic and fine-grained tokens |
| `google-api-key` | high | Google API keys (`AIza...`) |
| `template-example` | low | a copy-me template that never fires |

## Verification needed

The starter detectors were written from memory, not copied from provider
documentation. **Their formats need verification before you rely on them.** Each
detector file carries a `VERIFY` note and a documentation link. Formats that are
requested but **not implemented and not verified** are Stripe, Paystack, and
Flutterwave. Private key blocks (`-----BEGIN ... PRIVATE KEY-----`) are not
detected yet either, even though the skill's description mentions private keys.
See the verification lists in
[`references/adding-detectors.md`](skills/secret-scanner/references/adding-detectors.md).

## What this project does NOT do

- It does not send anything over the network.
- It does not print full secrets.
- It does not modify your files or rewrite git history on its own.
- It does not prove a project is safe.
- It is not for scanning code you do not own or have permission to review.

## Testing

```sh
python3 skills/secret-scanner/tests/run_tests.py
```

The tests build fake projects in a temporary directory. All secret-shaped
values are generated at run time so no realistic key is committed. See
[`tests/fixtures/README.md`](skills/secret-scanner/tests/fixtures/README.md).

## Roadmap and good first issues

- [ ] Verify and, where needed, correct the three starter detector formats.
- [ ] Add a Stripe detector after checking the current key format.
- [ ] Add a test case for a detector you did not write.

Small, well-scoped tasks are labelled `good first issue` in the issue tracker.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the Hacktoberfest-friendly guide to
claiming one. Roadmap items are plans, not promises.

## Contributing

Contributions are welcome, including documentation, tests, and one-detector
pull requests. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md) first. New contributors can follow the
[first contribution guide](docs/FIRST_CONTRIBUTION_GUIDE.md).

## Security

Report a vulnerability in the scanner through a private channel, and report a
missed or false detection as described in [SECURITY.md](SECURITY.md). Do not
open a public issue for a scanner vulnerability, and never paste a real secret
into any report.

## License

[MIT](LICENSE). Copyright (c) 2026 Anas Ishaq.

The community files in this repository were adapted from
[geekinks/open-source-project-template](https://github.com/geekinks/open-source-project-template),
which is released under MIT. See [Acknowledgements](#acknowledgements).

## Acknowledgements and attribution

- Community file structure adapted from
  [geekinks/open-source-project-template](https://github.com/geekinks/open-source-project-template)
  (MIT). The upstream project is a documentation starter; its own `LICENSE`
  file is an unfilled MIT template with no named copyright holder, so this
  repository keeps its own MIT notice and credits the source here.
- The Agent Skill layout follows the [Agent Skills specification](https://agentskills.io/specification).
- Secret detection is inspired by the idea behind tools such as gitleaks and
  trufflehog, but no code from them is included.
