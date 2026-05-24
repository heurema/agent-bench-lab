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
