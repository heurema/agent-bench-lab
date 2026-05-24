# Evaluation Protocol

## Paired comparison

When comparing two setups, run them on the same task seeds.

```text
Setup A on IF-01 case_001
Setup B on IF-01 case_001
Setup A on IF-01 case_002
Setup B on IF-01 case_002
```

This avoids confusing task difficulty with agent quality.

## Default repeats

| Task type | Repeats |
|---|---:|
| exact artifact tasks | 3 |
| stateful API/tool tasks | 5 |
| research/memory/interactive tasks | 7 |

## Freeze these per experiment

- model and provider version;
- temperature/top-p;
- system prompt hash;
- tool policy hash;
- task version;
- fixture version;
- seed;
- run budget;
- memory policy.

## Compare separately

Do not collapse everything into one score. Track:

- score;
- success;
- cost;
- latency;
- tool calls;
- failed tool calls;
- policy violations;
- hidden-case score;
- mutation-case score;
- repeated-run reliability.
