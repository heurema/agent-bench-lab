# Tasks

Each task directory contains:

```text
task.json   public task card
prompt.md   user-facing prompt template
scorer.py   public scorer interface or sample scorer
```

Public tasks are examples and development templates. Real evaluation should use private hidden cases under `private/` or another non-public storage location.
