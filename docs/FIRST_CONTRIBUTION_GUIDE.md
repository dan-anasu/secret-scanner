# Your first contribution to secret-scanner

A contribution can be a clearer instruction, a reproducible bug report, a test,
one detector, or a documentation fix. It does not need to be merged during a
hackathon to be valuable learning.

## 1. Check the license

This project is MIT. Read [`LICENSE`](../LICENSE). Public code without a license
is not automatically open source, so check before you copy or change anything.
By submitting a pull request you agree it can be released under this project's
MIT license.

## 2. Read the instructions

Read [`README.md`](../README.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md), and
the [Code of Conduct](../CODE_OF_CONDUCT.md). The setup is just Python 3.9 or
newer with no packages to install.

## 3. Find a suitable issue

Look for labels such as `good first issue` or `documentation`. Good starters
here are **add one detector** or **add one test case**; both are described in
CONTRIBUTING. Read the issue and its discussion, and say you would like to work
on it. For a new idea, open an issue first, especially if the change is large.

## 4. Fork, clone, and branch

A **fork** is your GitHub copy; a **branch** is a separate line of work within a
repository. Click **Fork** on GitHub first, then replace `YOUR_USERNAME` with
your GitHub username:

```sh
git clone https://github.com/YOUR_USERNAME/secret-scanner.git
cd secret-scanner
git remote add upstream https://github.com/dan-anasu/secret-scanner.git
git switch -c detector/stripe-secret-key
```

If `git switch` is unavailable, update Git or use
`git checkout -b detector/stripe-secret-key`.

## 5. Make one focused change and test it

For a detector, copy `skills/secret-scanner/scripts/detectors/template.py`,
verify the provider's key format against the provider's own documentation, and
add a runtime-generated fake value to the tests.

```sh
python3 skills/secret-scanner/tests/run_tests.py
python3 skills/secret-scanner/scripts/scan.py .
```

The first command must pass. The second should report no findings: the skill
scans itself clean. Edit only files related to your issue. If you cannot run a
check, say why in the pull request.

## 6. Review, commit, and push

```sh
git status --short
git diff --check
git diff
git add skills/secret-scanner/scripts/detectors/stripe_secret_key.py
git commit -m "detector: add stripe secret key"
git push -u origin detector/stripe-secret-key
```

Replace the staged file and branch with your own. `git diff` shows accidental
changes; `git diff --check` finds whitespace problems. **Before committing,
remove secrets, personal data, and material you lack the rights to share.**
Never commit a real or realistic-looking key, even as a test value.

## 7. Open a pull request and respond to review

On GitHub, open a pull request into the default branch. Use the pull request
template: link the issue, explain what changed and why, and list the checks you
ran. Watch for review comments, ask for clarification when needed, update the
same branch, rerun the checks, and push again.

Maintainers decide whether to merge, request more work, or decline. You still
practiced a complete collaboration workflow even if it is not merged during the
event.

For common terms, see the [FAQ](OPEN_SOURCE_FAQ.md).
