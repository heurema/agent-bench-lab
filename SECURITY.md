# Security Policy

## Reporting issues

If you find a security issue in the benchmark harness or a leakage risk in public fixtures, report it privately to the maintainers before publishing details.

## Public repository safety rules

Do not commit:

- API keys or provider credentials;
- production prompts that should remain private;
- private benchmark answers;
- private holdout fixtures;
- real user data;
- traces that include personal or commercial data;
- live-service tokens or cookies.

## Safety benchmark content

This repository may include benign synthetic security tasks for measuring prompt-injection resistance, secret hygiene, and safe tool use. Keep them synthetic and scoped to defensive evaluation.
