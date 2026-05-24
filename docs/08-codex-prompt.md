# Codex Prompt

Use this prompt when asking a coding agent to continue the repository setup.

```text
You are working on a public open-source repository called Agent Bench Lab.

Goal:
Turn this starter repository into a clean, public, community-friendly v0 for reproducible AI-agent evaluations.

Non-negotiable constraints:
- Do not add secrets, API keys, personal data, real emails, real calendar data, real financial data, or private traces.
- Do not commit hidden benchmark answers or private holdout fixtures.
- Keep public fixtures synthetic and clearly marked as examples.
- Keep private/hidden/holdout data under gitignored paths only.
- Prefer deterministic scoring over LLM judging.
- Keep the first version small and local-first.
- Do not introduce live-service dependencies for benchmark-critical tasks.

Primary tasks:
1. Review the repository structure and keep it simple.
2. Move or consolidate documentation into docs/ with clear filenames and cross-links.
3. Improve README.md so a new contributor understands:
   - what the project is;
   - why repeated agent evaluation matters;
   - how public/private benchmark data is separated;
   - how to run validation and scoring smoke tests.
4. Implement or improve the CLI commands:
   - list-tasks;
   - validate;
   - score;
   - optionally compare-runs later.
5. Ensure task.json files validate against schemas/task.schema.json.
6. Make scorers follow one interface:
   score(task_dir, fixture_dir, artifacts_dir) -> dict
7. Add tests for registry loading, task validation, and sample scorers.
8. Keep the core suite focused on six task families:
   - CODE-01 Local regression patch
   - TERM-02 Log-driven config repair
   - APP-04 Airline rebooking under policy
   - DATA-01 CSV + SQL memo
   - IF-01 Long spec contract artifact
   - SEC-01 Hidden prompt injection in HTML/email
9. Add a public release checklist and leak-check script if missing.
10. Do not overbuild browser, MCP, multi-agent, or deep-research infrastructure yet.

Implementation style:
- Use Python standard library where practical.
- Keep dependencies minimal.
- Write clear errors.
- Make the project runnable locally.
- Prefer small, composable modules.
- Include comments only where they clarify non-obvious design choices.

Before finishing:
- Run validation.
- Run tests if available.
- Run the public leak-check script.
- Summarize what changed and what remains for v0.1.
```
