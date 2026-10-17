# Security Policy

## Scope

This policy covers two very different things:

1. **A vulnerability in the scanner itself** - code execution, a crash on
   hostile input, a path that reads beyond what you asked for, a network call
   that should not exist, or a redaction bug that leaks a secret it promised
   to hide. Report these privately.
2. **A detection problem** - a real secret the scanner missed (a false
   negative) or a value it flagged that is not a secret (a false positive).
   Most of these are normal bug reports and can be filed in the public issue
   tracker, unless the report itself contains a real credential.

Never paste a real secret, private key, or personal data into any report,
public or private. Redact it first.

## Supported versions

| Version or branch | Security fixes? |
| --- | --- |
| `main` | Yes |
| Tagged `0.x` releases | Best effort |
| Older forks and copies | No |

Support means maintainers intend to consider security fixes. It is not a
response-time promise.

## Report a vulnerability privately

Use GitHub's private vulnerability reporting on the **Security** tab, or open
an advisory directly:

    https://github.com/dan-anasu/secret-scanner/security/advisories/new

If that channel is unavailable, contact the maintainer and agree on a private
medium before sending details. Do not use a public issue or pull request for
exploit details.

Include a concise description, the affected version or commit, steps to
reproduce, the likely impact, and any safe proof of concept. State whether data
may have been exposed. Remove credentials, personal data, and unnecessary
exploit payloads.

## Report a missed or false detection

A missed detection (false negative) and a wrong flag (false positive) are both
welcome. Use the **Bug report** or **Detector request** issue form, or open an
issue directly.

- **Missed detection:** say which provider or credential type, and describe the
  shape of the value. **Do not paste the real secret.** Build a fake value with
  the same shape (for example, replace random characters) and paste that.
- **False positive:** paste the exact line with the secret-looking value
  replaced by `REDACTED`, and say why the value is not a secret (for example,
  it is a documented example, a checksum, or a public identifier).
- **Wrong format in a detector:** link the provider's current documentation.
  Detectors are only as good as the format they encode.

Reports that include a real secret will be edited or closed, and the reporter
will be asked to rotate the credential.

## Response and disclosure

Maintainers will acknowledge a report when they can, reproduce it, coordinate a
fix, and agree with the reporter on responsible public disclosure. Details that
would help exploitation are not published before users have had a reasonable
chance to update. No fixed response or resolution time is promised.

## The scanner's own safety properties

These are design promises. A break in any of them is a vulnerability:

- The scanner makes **no network calls**.
- The scanner **never prints a full secret**; matches are redacted to the first
  four characters plus a fixed-width mask.
- The scanner **never writes to or deletes** the files it scans.
- The scanner runs detector files from its own `detectors/` directory only, and
  treats a broken detector as a warning rather than executing arbitrary code
  from the scanned project.

A clean scan is not proof of safety. No scanner catches every secret, and this
policy does not claim otherwise.
