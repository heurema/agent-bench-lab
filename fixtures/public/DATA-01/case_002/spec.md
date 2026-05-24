# DATA-01 Case 002: Duplicates, Nulls, And Boundaries

Use the synthetic files under `data/`:

- `events.csv`
- `customers.csv`
- `analytics.db`

Produce exactly these artifacts and no others:

- `metrics.json`
- `report.md`
- `chart_spec.json`

## Metric Rules

Use only rows where:

- `event_type` is `purchase`;
- `status` is `paid`;
- `occurred_at` is inside May 2026, including both boundary timestamps;
- `revenue_usd` is non-empty;
- the customer exists in `customers.csv`;
- the product exists in the SQLite `product_catalog` table.

Deduplicate repeated `event_id` rows by keeping the first occurrence.
Normalize region values by trimming whitespace and uppercasing.
Break ties alphabetically.

`metrics.json` must include:

- `qualified_event_count`
- `duplicate_event_ids_ignored`
- `null_revenue_event_count`
- `boundary_event_count`
- `total_revenue_usd`
- `top_region_by_revenue`
- `revenue_by_region`
- `top_category_by_revenue`

Round currency values to two decimals.

## Report Rules

`report.md` must include these headings in order:

- `# DATA-01 Case 002 Memo`
- `## Summary`
- `## Data Quality`
- `## Caveats`

The report must mention the duplicate event id, null revenue count, boundary event count, total revenue, and top region.
Do not mention profit, margin, forecasts, or conversion rates.

## Chart Rules

`chart_spec.json` must describe revenue by region with deterministic data:

- title: `Case 002 Revenue by Region`
- x-axis: `region`
- y-axis: `revenue_usd`
- one series named `revenue_usd`
