# Project maintainer checklist

Adapted from the [geekinks/open-source-project-template](https://github.com/geekinks/open-source-project-template)
checklist (MIT). Maintainers set direction, review contributions, publish
releases, and care for the community.

Sole maintainer: **Anas Ishaq**. State co-maintainers here if that changes, and
say who can merge and release.

## Before launch

- [x] Define the project's problem, intended users, scope, current limitations,
  and a small first milestone. See the [README](../README.md).
- [x] Choose a software license and fill in the copyright details. MIT,
  Copyright (c) 2026 Anas Ishaq.
- [x] Review third-party material for rights and attribution. No copied code;
  community files adapted from an MIT template and credited.
- [x] Replace bracketed values in the README and community files. Owner
  (`dan-anasu`) and conduct contact are filled in.
- [x] Verify a fresh contributor can set up the project. No install step;
  Python 3.9+ only.
- [x] Set a real private conduct contact and a working security channel.
  Security uses GitHub private vulnerability reporting (enable it in Settings,
  Security after the first push); the conduct contact is
  anasishaq7110@gmail.com.
- [ ] Decide how issues are triaged, who reviews pull requests, and who can
  merge or release. Currently one maintainer.
- [ ] Create two or three starter issues with acceptance criteria and a label.
  The tasks are listed in [CONTRIBUTING.md](../CONTRIBUTING.md); create them on
  GitHub.
- [x] Automate tests in CI and keep a local command. See
  [`.github/workflows/test.yml`](../.github/workflows/test.yml).
- [x] For AI work, review model, dataset, API, dependency, and asset terms.
  Not applicable here: the project ships no model, dataset, or API usage.

## During maintenance

- [ ] Welcome contributors, respond respectfully, and give actionable reviews.
- [ ] Keep setup steps, supported versions, roadmap, and limitations current.
- [ ] Review security reports privately and coordinate fixes and disclosure.
- [ ] Tag releases, publish change notes, and explain breaking changes.
- [ ] Recheck third-party terms when adding material.
- [ ] State realistic review capacity; add co-maintainers or reduce scope if
  needed.
- [ ] If the project is archived, say so prominently and explain whether issues
  and security reports are still monitored.

Use the [release checklist](OPEN_SOURCE_CHECKLIST.md) before public launches and
major releases.
