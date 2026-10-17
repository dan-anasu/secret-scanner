---
name: secret-scanner
description: Scans a local project for leaked secrets such as passwords, API keys, tokens, and private keys before the user pushes code to GitHub. Use when the user says check my repo for secrets before I push, did I leave any API keys in my code, or scan this project for passwords. Runs a bundled offline Python scanner, triages each finding as a real secret or a likely placeholder, and guides the user through rotation and cleanup. Not for hunting secrets in code the user does not own or have permission to review, and never a guarantee that a clean scan means the project is safe.
license: MIT
---

# Secret Scanner

Find leaked secrets in a project the user is about to publish, separate real
credentials from placeholders, and walk the user through fixing them.

The scanner is a bundled, dependency-free Python 3 script. It runs offline.
It never opens a network connection and never sends file contents or findings
anywhere.

## When to use this skill

Use it when the user wants to check a project before publishing it. Typical
requests:

- "check my repo for secrets before I push"
- "did I leave any API keys in my code"
- "scan this project for passwords"

## When NOT to use this skill

- Do not scan code the user does not own or does not have permission to review.
- Do not present a clean scan as proof that the project is safe. No scanner
  catches every secret.
- Do not edit the user's files or rewrite git history without explicit
  confirmation.

## Gather first

Ask only for what is missing:

1. **Project path** to scan. Default to the current working directory.
2. **Include git history?** History finds secrets that were deleted but are
   still in old commits. It is slower and needs `git`. Default to yes if the
   folder is a git repository, but confirm first.
3. **Is the repository already public?** If it is, say so plainly: the secret
   may already be copied, and rotation is urgent. If it is private, explain
   that making it public later still exposes the history.

## Process

1. **Confirm scope.** Do not start until you know the path, the history
   choice, and the visibility.
2. **Run the scanner.** From the skill directory:

   ```sh
   python3 scripts/scan.py <project-path>
   python3 scripts/scan.py <project-path> --history
   ```

   Use `--json` when you need to process the results, and `--quiet` for just
   the summary line. The exit code is 1 when there are findings, so a shell
   `&&` chain will stop on purpose.
3. **Read the report.** The scanner already redacts every match to the first
   four characters plus asterisks. Keep it redacted.
4. **Triage each finding: real secret or placeholder?** Look at the variable
   name, the file, and the surrounding context. Test fixtures, documentation,
   and example files often contain fake values. If you are unsure, ask the
   user rather than guessing.
5. **Fix real secrets in this order** (details in
   [references/remediation.md](references/remediation.md)):
   1. Rotate or revoke the credential. Deleting the file does not invalidate
      a leaked secret.
   2. Move the value into an environment variable or a secrets manager.
   3. If it was committed, clean the git history and force-push, then tell
      collaborators to re-clone.
   4. Add prevention: `.gitignore` plus a pre-commit hook or CI check.
6. **Report** using the format below, then remind the user that no scanner
   catches everything.
7. **Offer prevention**, and only apply it after the user agrees.

## Output format

Produce a short report, not a wall of text.

**Summary line.** Counts by severity, for example:
`3 critical, 1 high, 0 medium, 2 low`.

**Findings table.**

| File | Line | Detector | Severity | Redacted match | Verdict |
| --- | --- | --- | --- | --- | --- |
| src/config.py | 12 | github-token | critical | `ghp_******` | needs review |
| .env.example | 3 | generic-assignment | medium | `sk_t******` | likely placeholder |

**Prioritized remediation checklist.** Rotate or revoke first, then move the
value, then clean history if it was committed, then add prevention.

End with the limitation: a clean scan does not prove the project is safe.

## Rules

- **Never print a full secret.** Show the redacted form only, with the file
  path and line number. This applies in chat, in summaries, and in any file
  you write.
- **Never send file contents or findings to a network service.** Do not paste
  them into a search, an API, or an issue template.
- **Never claim a clean scan proves safety.** Say no scanner catches
  everything.
- **Never modify user files or rewrite git history** without explicit
  confirmation, and tell the user to back up or re-clone first.
- **Refuse out-of-scope requests.** Do not use this skill to find secrets in
  code the user does not own or have permission to review.

## What is in this skill

- `scripts/scan.py` - the scanner. Dependency-free Python 3.
- `scripts/detectors/` - one file per detector. Three starters (AWS, GitHub,
  Google) plus a documented template.
- `references/remediation.md` - how to rotate, store, and clean up secrets.
- `references/adding-detectors.md` - how to add a detector and verify formats.
- `tests/` - self-contained tests. Fixtures generate fake secrets at runtime so
  no realistic key is ever committed.

Run the tests with `python3 tests/run_tests.py`.
