# Canonical Scope and Consumer Boundary

Agent Bench Lab is the canonical repository for benchmark task-family standards.

It is product-neutral and domain-agnostic.

Any consumer application can use Agent Bench Lab to run benchmarks, present results, manage users, or mount private eval bundles. Consumer applications should not create parallel benchmark definitions or scorer formats.

## What belongs in Agent Bench Lab

- task-family standards and definitions;
- public synthetic examples;
- fixture conventions;
- scorer interfaces;
- run, trace, and score formats;
- comparison protocol;
- anti-overfitting guidance;
- public/private split rules.

## What belongs in the Private Eval Layer

The Private Eval Layer is a boundary, not a required implementation.

It may be a gitignored local folder, private repository, encrypted bundle, customer-scoped storage, or enterprise eval service.

It owns:

- private holdouts;
- hidden labels;
- answer keys;
- protected scorer configs;
- canaries;
- customer-specific checks;
- private rubrics;
- redaction rules;
- customer-scoped fixtures.

## What belongs in consumer applications

- product UX;
- agent setup management;
- customer onboarding;
- permissions;
- task packet delivery;
- artifact upload;
- customer-specific private bundle mounting;
- scheduled runs;
- dashboards and recommendations.

## Customer-specific checks

Customer-specific checks should be private bundles mounted at run time.

They should not be committed to public repositories, shown to the agent, or mixed into generic public examples.

Consumer applications can keep references, hashes, bundle versions, permissions, and result summaries. Agent Bench Lab should remain the source of truth for task-family format, scorer semantics, run records, trace expectations, comparison rules, and public/private hygiene.

Agent Bench Lab should not know which consumer application uses it.

## Standard Layer Contracts

Agent Bench Lab should define:

- private eval boundary expectations;
- scorer type contracts;
- normalized score records;
- trace and report expectations;
- redacted feedback rules;
- decision-grade graduation criteria.

The protected content itself belongs in the Private Eval Layer. User interaction, scheduling,
permissions, task delivery, and report display belong in consumer applications.
