# Architecture

The MVP architecture is intentionally small.

```text
task card + fixtures + runner + agent adapter + tools + trace logger + scorer + report
```

## Components

| Component | Job |
|---|---|
| Task registry | Lists available tasks and metadata |
| Fixtures | Versioned inputs, seeds, and snapshots |
| Runner | Resets environment and invokes the agent |
| Agent adapter | Normalizes model/provider/scaffold calls |
| Tool adapter | Wraps bash/browser/function/MCP tools |
| Trace logger | Records model calls, tool calls, outputs, and timings |
| Scorer | Produces deterministic or semi-deterministic scores |
| Report generator | Compares runs and produces summaries |
| Artifact store | Saves generated files for replay and diffing |

## v0 rule

Do not overbuild the runner before task scoring works. Start with direct artifact scoring, then add agent adapters.

## Benchmark standard vs consumer application

Agent Bench Lab should stay product-neutral.

It defines the benchmark standard:

```text
task registry conventions
fixture conventions
scorer interfaces
run records
trace format
comparison reports
public/private rules
```

Consumer applications can wrap this standard with:

```text
UI
onboarding
agent setup management
scheduled runs
permissions
customer-specific private bundle mounting
dashboards
recommendations
```

Consumer applications should not create a separate benchmark taxonomy or scorer format. If a new task family is useful, define it in Agent Bench Lab first, then let consumer applications consume it.
