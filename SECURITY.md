# Security policy

## Supported version

Security fixes are prepared for the latest `1.0K` release line.

## Reporting a vulnerability

Do not open a public issue containing exploit details or personal data. Use the
repository owner's private GitHub security advisory channel after the repository
is published.

Include the affected format, a minimal reproduction archive, expected impact,
and the Crow Pack and Python versions. Remove unrelated personal files before
sharing a sample archive.

## Archive safety limits

Crow Pack treats archive names and contents as untrusted. It blocks absolute and
parent-relative paths, links, Windows device names, case-insensitive collisions,
more than 100,000 entries, files larger than 8 GiB, total output larger than
32 GiB, and suspicious compression ratios. Executable files cannot be launched
directly from the archive preview.

Image previews are limited to 20 MiB and 40 million pixels. PDF optimization
refuses encrypted or digitally signed documents and never overwrites the source.
