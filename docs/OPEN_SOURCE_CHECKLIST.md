# Open-source release checklist (completed)

Adapted from the [geekinks/open-source-project-template](https://github.com/geekinks/open-source-project-template)
checklist (MIT). Each item below states the project's current answer. Items
marked **[needs you]** cannot be completed by code alone.

## Code and rights

- [x] **Repository is public when ready, with no secrets, private data, or files
  included by mistake.** The scanner self-scans clean (0 findings). The
  repository is `dan-anasu/secret-scanner`.
- [x] **A suitable software license is present and names the correct copyright
  holder(s).** `LICENSE` is MIT, "Copyright (c) 2026 Anas Ishaq". The starter
  MIT text from the template was reviewed; its placeholders were not copied.
- [x] **Ownership and permission to redistribute contributed code, copied code,
  and generated material are clear.** All scanner and skill code is original.
  Community files are adapted from an MIT-licensed template and credited in
  `README.md` and `CONTRIBUTING.md`. No code was copied from other secret
  scanners.
- [x] **Dependency licenses, notices, and compatibility have been reviewed.**
  There are no third-party dependencies. The scanner uses only the Python
  standard library.
- [x] **Images, fonts, documentation, data, and other assets have source,
  attribution, and separate terms recorded where needed.** The project ships no
  images, fonts, or datasets.

## Usable project and community

- [x] **README explains the problem, users, setup, usage, limitations, and
  actual project status.** See `README.md`, including the "Status" and
  "Verification needed" notes.
- [x] **Installation and tests work from a fresh clone using documented
  commands.** No install needed. `python3 skills/secret-scanner/tests/run_tests.py`
  passes (17 tests). Honest caveat: verified on Python 3.14 only; Python 3.9+
  is claimed and the CI matrix covers 3.9 and 3.12, but 3.9 has not been run
  locally.
- [x] **Contribution guidelines, Code of Conduct, and a real private security
  reporting channel are ready.** `CONTRIBUTING.md` and `SECURITY.md` are done.
  `CODE_OF_CONDUCT.md` uses the maintainer's email
  (anasishaq7110@gmail.com). `SECURITY.md` uses GitHub private vulnerability
  reporting, which works as soon as the repository exists.
- [x] **Issue forms and the pull request template match the project's
  workflow.** Bug report, feature request, and a project-specific detector
  request form, plus the PR template.
- [ ] **Maintainers know who reviews issues and pull requests, makes release
  decisions, and moderates discussions.** Sole maintainer: Anas Ishaq. **[needs
  you]** decide whether to add co-maintainers and state it in the README.
- [ ] **Useful small starter issues have context, expected outcome, and a way to
  check the result.** Good first issues are described in `CONTRIBUTING.md`.
  **[needs you]** create them as real GitHub issues and add `good first issue`.
- [x] **Relevant tests and continuous integration run where practical.**
  `tests/run_tests.py` runs locally, and `.github/workflows/test.yml` runs the
  suite plus a self-scan on push and pull request.

## Releases, safety, and honesty

- [x] **Known limitations, accessibility gaps, privacy practices, data
  handling, and security risks are documented.** The README, `SKILL.md`, and
  `SECURITY.md` state that the tool is offline, redacts matches, never modifies
  files, and cannot prove safety.
- [x] **Release tags and versioning approach are defined; breaking changes and
  migration steps will be announced.** `CHANGELOG.md` follows Keep a Changelog;
  SemVer is the stated approach. **[needs you]** no release tag exists yet.
- [x] **Maintainers can publish fixes, review security reports privately, and
  explain the project's maintenance status.** Described in `SECURITY.md` and
  `CONTRIBUTING.md`.

## AI projects, if applicable

- [x] **Distinguish the application source-code license, model-weight license or
  usage terms, dataset license and provenance, dependency and asset licenses,
  and proprietary API terms.** The application code is MIT. The project ships
  **no model weights, no datasets, and no proprietary API usage**. The skill is
  plain instructions plus a local scanner, so there are no model terms to state.
- [x] **Complete a real AI model card with exact model version, publisher,
  inference location, runtime and hardware needs, data flows, evaluation
  evidence, limitations, and human oversight.** **Not applicable:** no model is
  shipped or called. The scanner makes no network calls and has no inference
  step, so there is nothing to fill in. The template's AI model card was
  intentionally skipped.
- [x] **Verify whether weights are actually available and under what
  conditions.** **Not applicable:** no weights. Stated plainly so nobody assumes
  otherwise.
- [x] **For an agent-skill category, show the skill's original behavior and how
  it follows the Agent Skills Open Standard.** `README.md` ("The Agent Skill")
  describes the original behavior. `skills/secret-scanner/SKILL.md` follows the
  frontmatter and directory rules from
  [agentskills.io/specification](https://agentskills.io/specification) and
  validates with the reference `agentskills validate` command.

## Summary of what is left for the maintainer

1. Create the GitHub repository (done: `dan-anasu/secret-scanner`), then enable
   private vulnerability reporting under Settings, Security.
2. Create the starter issues and label them `good first issue`.
3. Decide the release tag for the first version.
4. Optionally verify the detector formats against provider documentation.
   Private keys (PEM blocks) and Stripe, Paystack, and Flutterwave still need
   detectors.
