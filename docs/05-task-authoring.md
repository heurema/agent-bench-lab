# Task Authoring Guide

A good task is not just a prompt. It is a package:

```text
instruction + fixtures + allowed tools + forbidden actions + expected artifact + scorer + trace policy
```

## Task card minimum

Each task needs:

- ID and version;
- category;
- purpose;
- agent role;
- user prompt;
- public fixture paths;
- expected artifact shape;
- scoring rubric;
- hidden/mutation strategy;
- failure modes;
- logging requirements.

## Prefer

- local data;
- synthetic fixtures;
- exact JSON/artifact formats;
- state diff scoring;
- fast tests;
- meaningful hidden checks;
- seeded variants.

## Avoid

- vague tasks with no oracle;
- live websites without snapshots;
- LLM-only scoring as the primary oracle;
- tasks that require private user data;
- hidden answer keys in public repos.
