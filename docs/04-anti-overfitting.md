# Anti-overfitting Controls

The biggest benchmark risk is not that the model magically learns during a run. The bigger risk is that the developer tunes prompts, memory, tool policies, or scaffolds against the same public examples until the setup is good at the benchmark but not at the underlying task family.

## Basic split

```text
public visible cases  -> development and debugging
private hidden cases  -> final comparison
mutation cases        -> brittleness check
canary cases          -> leakage detection
```

## Rules

1. Never make final decisions using only cases you used for prompt tuning.
2. Keep hidden holdouts out of the public repository.
3. Clear or isolate memory between runs unless memory is the thing being tested.
4. Do not give agents prior score reports or successful traces.
5. Use task generators and seeds where possible.
6. Rotate private fixtures when a public task becomes too familiar.
7. Add canary strings to detect accidental leakage into memory or traces.

## Warning signs

| Observation | Interpretation |
|---|---|
| visible score improves, hidden score does not | likely overfit |
| hidden score improves, cost triples | conditional improvement |
| mutation score drops sharply | brittle improvement |
| memory recalls benchmark answers | invalid run |
| same setup passes once but fails often | reliability problem |
