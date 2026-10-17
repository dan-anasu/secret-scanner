# Remediation guide

Use this when a finding is confirmed as a real secret. The order matters:
the steps below are ranked from most urgent to least.

## 1. Rotate or revoke the credential first

Deleting a file, adding it to `.gitignore`, or rewriting history does not
invalidate a leaked secret. Anyone who already copied it can still use it.

- Revoke the old credential at the provider, then create a new one.
- If the credential is shared or long-lived, revoke everything that used it and
  reissue.
- Check the provider's audit log or usage report for unexpected activity, and
  raise the issue with whoever owns the account if you are not the owner.

Where to rotate, by provider (verify the current page before relying on it):

| Provider | Where to revoke |
| --- | --- |
| AWS | IAM console, Access keys per user, or the Security Token Service for temporary keys |
| GitHub | Settings, Developer settings, Personal access tokens or GitHub Apps |
| Google Cloud | Console, APIs and Services, Credentials (API keys and OAuth clients) |
| Stripe | Dashboard, Developers, API keys (roll the key and update webhooks) |
| Paystack | Dashboard, Settings, API Keys and Webhooks |
| Flutterwave | Dashboard, Settings, API Keys |

If the credential is a database password, change it in the database, then
update every app that connects. If it is a private key, generate a new key
pair and remove the old public key from the service.

## 2. Move the value out of the code

Replace the literal with a lookup at runtime.

- Local development: an environment variable loaded from a file that is ignored
  by git (`.env`), or your shell.
- Production: a secrets manager such as AWS Secrets Manager, GCP Secret
  Manager, HashiCorp Vault, 1Password, Doppler, or your platform's built-in
  secret store.
- CI: the platform's secret or variable store, never a value in the workflow
  file.

Keep a committed `.env.example` with placeholder values so new contributors
know which variables exist. Never put a working value in it.

## 3. Clean the git history if it was committed

Only do this with the user's explicit consent, and after they have a backup or
a fresh clone. History rewriting changes every commit hash and requires a
force-push.

- Back up the repository first, or work in a copy.
- Rewrite with `git filter-repo` (preferred) or BFG Repo-Cleaner. Both replace
  the secret text in all commits, then you force-push.
- If the repository is shared, tell every collaborator to re-clone. Their old
  clones still contain the secret and will reintroduce it on the next push.
- If the secret is already live, rotation still comes first. Cleaning history
  only limits future copies; it cannot recall copies that already exist.

## 4. Add prevention

- Add the file or pattern to `.gitignore`.
- Add a pre-commit hook or a CI job that runs this scanner and fails the build
  on findings. The scanner exits non-zero when it finds something, so it drops
  straight into a check.
- Turn on the host's push protection (for example GitHub secret scanning and
  push protection) for the project.

## Honesty note

No scanner catches every secret. A clean report lowers risk; it does not prove
the project is safe. Say this to the user every time.
