# Test fixtures

Fixtures here generate fake secrets at runtime. Nothing in this directory is a
real credential.

Why runtime generation: committing a realistic-looking key, even a fake one,
can trip GitHub push protection and teaches contributors bad habits. Instead,
`generate_fixtures.py` builds format-shaped values from random characters each
time the tests run, writes them into a temporary directory, and the tests
assert that the scanner finds them.

The formats used (AWS, GitHub, Google) mirror the shipped detectors. Those
formats are written from memory and still need verification against provider
documentation. See `references/adding-detectors.md`.
