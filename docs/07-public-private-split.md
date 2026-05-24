# Public / Private Split

This repository is intended to be public from the beginning.

## Public files

Public files should include:

- documentation;
- schemas;
- task templates;
- synthetic public sample fixtures;
- scorer interfaces;
- fixture generators;
- public examples.

## Private files

Private files should not be committed:

- hidden fixtures;
- holdout seeds;
- private answer keys;
- traces from real tasks;
- real user or customer data;
- production prompts;
- provider keys.

## Recommended local layout

```text
private/
  fixtures/
    APP-04/
      case_101/
      case_102/
  answer_keys/
  reports/
```

`private/` is gitignored by default.
