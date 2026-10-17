# Contributing

Thanks for helping. This project welcomes first-time contributors and is set up
for [Hacktoberfest](https://hacktoberfest.com/). Contributions can be code,
tests, detector files, documentation, or a good bug report.

Read the [Code of Conduct](CODE_OF_CONDUCT.md) first. New contributors can
follow the [first contribution guide](docs/FIRST_CONTRIBUTION_GUIDE.md).

> Maintainer: the upstream repository is `dan-anasu/secret-scanner`, and the
> conduct contact is set in `CODE_OF_CONDUCT.md`.

## Good first issues

Small, self-contained tasks. Each is one focused pull request.

- **Add one detector.** Copy `skills/secret-scanner/scripts/detectors/template.py`,
  verify a provider's key format against the provider's own documentation, and
  add the file. Link the documentation in the module docstring.
- **Add one test case.** Extend `skills/secret-scanner/tests/run_tests.py` with a
  case for a detector or an edge case that is not covered yet.
- **Fix a "verify" note.** Open a detector, confirm the format against the
  provider docs, and update the docstring with the link.
- **Improve a reference.** Tighten wording in
  `skills/secret-scanner/references/`.
- **Report a false positive or a missed detection** using the issue forms.

Say in the issue that you would like to work on it. Assignment is coordination,
not a guarantee of acceptance.

## Set up a local copy

1. On GitHub, select **Fork** to create a copy under your account.
2. Replace only `YOUR_USERNAME` with your GitHub username:

   ```sh
   git clone https://github.com/YOUR_USERNAME/secret-scanner.git
   cd secret-scanner
   git remote add upstream https://github.com/dan-anasu/secret-scanner.git
   git switch -c detector/stripe-secret-key
   ```

3. There is nothing to install. Python 3.9 or newer is all you need.

## Run the tests

```sh
python3 skills/secret-scanner/tests/run_tests.py
```

All tests must pass. Run the scanner on itself too, which should stay clean:

```sh
python3 skills/secret-scanner/scripts/scan.py .
```

## Add a detector

See [`references/adding-detectors.md`](skills/secret-scanner/references/adding-detectors.md)
for the file format and the rules. The short version:

1. Copy `detectors/template.py` and rename it.
2. Set `NAME`, `SEVERITY`, and `PATTERN`.
3. **Verify the format against the provider's official documentation** and put
   the link in the docstring. Do not copy a format from a blog post or from
   another scanner.
4. Add a test with a fake value generated at runtime.

## Never commit a real or realistic secret

This is the one rule that matters most here.

- Do not put a real credential in code, tests, documentation, an issue, a pull
  request, a log, or a screenshot.
- Do not commit a realistic-looking key either, even a fake one. GitHub push
  protection may flag it and it teaches the wrong habit.
- Generate test values at run time from random characters. See
  `tests/fixtures/generate_fixtures.py`.
- If you find a real secret, follow [SECURITY.md](SECURITY.md) instead of
  opening a public issue.

## Make a focused change

- One topic per pull request.
- Run the tests and the self-scan above before pushing.
- Review your diff:

  ```sh
  git status --short
  git diff --check
  git diff
  ```

- Use a clear commit message, for example `detector: add stripe secret key` or
  `docs: clarify the allowlist format`.

## Open a pull request

Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md): link the
issue, explain the change, and list the checks you ran. A pull request is a
proposal; maintainers review it and decide whether to accept it. If reviewers
ask for changes, update the same branch and push again.

## Rights and attribution

Submit only material you have the right to share. Do not paste code from
another repository just because it is public: check its license and keep any
required notices. Record the source for anything you adapt. Community files in
this repository were adapted from
[geekinks/open-source-project-template](https://github.com/geekinks/open-source-project-template)
(MIT); keep the credit in `README.md` and this section when editing them.

## Questions

Open an issue with the `question` label, or ask in your pull request. Be
specific and be kind. Assume good intent, and respect different experience
levels and backgrounds.
