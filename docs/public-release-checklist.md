# Public Release Checklist

Use this before pushing to a public repository.

## Files

- [ ] No `.env`, API key, credential, cookie, token, or private config files.
- [ ] No real emails, calendars, financial records, user profiles, or customer data.
- [ ] No private traces from real agent runs.
- [ ] No hidden answer keys or private holdout fixtures.
- [ ] No local `runs/`, `traces/`, `artifacts/`, or generated reports.

## Benchmark integrity

- [ ] Public fixtures are clearly marked as examples.
- [ ] Hidden/private fixtures live outside the public repo or under gitignored directories.
- [ ] Task cards explain scoring without revealing private answers.
- [ ] Scorers are deterministic or clearly mark any rubric/LLM-assisted component.

## Documentation

- [ ] README explains public/private split.
- [ ] Docs explain anti-overfitting controls.
- [ ] Contribution guidelines warn against committing private benchmark data.
