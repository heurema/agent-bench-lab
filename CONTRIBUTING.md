# Contributing

Contributions are welcome, but this project has a strict public-safety rule:

> Do not contribute private user data, production secrets, hidden benchmark answers, or private holdout fixtures.

## Good contributions

- new public task templates;
- deterministic scorers;
- fixture generators;
- runner/scorer improvements;
- documentation;
- anti-overfitting and leakage checks;
- public sample tasks with synthetic data.

## Avoid

- live-service dependencies for benchmark-critical tasks;
- personal data;
- real emails, calendars, financial records, customer data, or repository secrets;
- scorer logic that depends on a non-reproducible LLM judgment;
- hidden answers committed to public branches.

## Contribution checklist

Before opening a PR:

1. Run `python scripts/public_leak_check.py .`.
2. Run `agent-bench validate`.
3. Confirm all new fixtures are synthetic.
4. Confirm no `.env`, API key, trace, or private holdout was committed.
5. Explain how the task is scored and what failure modes it reveals.
