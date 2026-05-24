# Canonical Scope and Baseline Boundary

Agent Bench Lab is the canonical repository for benchmark task families.

It is intentionally product-neutral and domain-agnostic.

Baseline and other products may use Agent Bench Lab to run benchmarks, present results, and manage customer-specific private bundles. They should not create parallel benchmark definitions or scorer formats.

## What belongs in Agent Bench Lab

- task-family definitions;
- public synthetic examples;
- fixture conventions;
- scorer interfaces;
- run, trace, and score formats;
- comparison protocol;
- anti-overfitting guidance;
- public/private split rules.

## What belongs in Baseline

- product UX;
- agent setup management;
- customer onboarding;
- permissions;
- customer-specific bundle mounting;
- scheduled runs;
- dashboards and recommendations.

## Customer-specific checks

Customer-specific checks should be private bundles mounted at run time.

They should not be committed to public repositories, shown to the agent, or mixed into generic public examples.

Baseline can keep references, hashes, bundle versions, permissions, and result summaries. Agent Bench Lab should remain the source of truth for task-family format, scorer semantics, run records, trace expectations, comparison rules, and public/private hygiene.
