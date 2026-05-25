# Research Radar Watchlist

Priorities:

- `P0 daily`: high-signal benchmark mechanics sources.
- `P1 weekly`: useful secondary sources and teams.
- `P2 monthly`: standards, conference tracks, and lower-cadence sources.

## P0 Daily

| Source group | Why monitor | Tags |
|---|---|---|
| SWE-bench ecosystem | Verified splits, issue curation, coding-agent evaluation methodology | code, verified, hidden-tests |
| Terminal-Bench | Terminal workflow tasks, executable environments, shell-based scoring | terminal, execution, replay |
| BrowserGym / AgentLab / WorkArena / WebArena-Verified | Browser and workplace-agent benchmarks, replay and verified environment patterns | browser, workflow, verified |
| OSWorld / OSWorld-Verified | Desktop/OS agent tasks, environment replay, verification issues | os, desktop, replay |
| AppWorld | API/app simulation, state-diff scoring, tool-use planning | api, state-diff, tools |
| MCP benchmark cluster | MCP/tool registry benchmarks and local tool-use evaluation patterns | mcp, tool-use, registry |
| Deep Research benchmark cluster | Fixed-corpus research, citation checks, claim scoring, long-horizon research tasks | research, citations, claims |
| AgentDojo / security cluster | Prompt injection, tool-output trust boundary, agent safety evals | security, injection, leaks |
| NIST / Inspect AI / standards | Eval framework practices, auditability, safety and policy measurement | standards, harnesses |
| Benchmark-hardening and exploit papers | Contamination, reward hacking, eval awareness, public benchmark exploitation | hardening, exploit, contamination |

## P1 Weekly

| Source group | Why monitor | Tags |
|---|---|---|
| Official benchmark issue trackers | Failure reports, validation fixes, exploit reports | bugs, validation |
| Eval framework releases | Harness, scoring, report, and trace-format ideas | framework, reporting |
| Author pages for benchmark maintainers | New papers before repos are updated | papers, authors |
| Workshop pages for agents/evals/safety | New accepted papers and benchmark tracks | conference, workshop |
| Model-system eval reports | Useful methodology, even when benchmark code is unavailable | methodology, reports |

## P2 Monthly

| Source group | Why monitor | Tags |
|---|---|---|
| Conference proceedings | Broad benchmark trends and new task families | survey, papers |
| Standards organizations | Slow-moving guidance for eval governance and reporting | standards, governance |
| Public leaderboards | Detect benchmark saturation or exploit incentives | leaderboard, integrity |
| Archived benchmark repos | Deprecation lessons and reproducibility failures | lifecycle, deprecation |

## Alert Rules

Open an issue when a source introduces:

- a new verified split;
- a new exploit or contamination finding;
- a new deterministic/state-based oracle pattern;
- a new replay/snapshot environment pattern;
- a new redacted-feedback or private-holdout method;
- a benchmark lifecycle or deprecation policy worth adapting.

Do not open issues for generic model score changes unless the method changes.
