# DATA-01 Case 003: CSV And SQLite Join

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
- `occurred_at` is inside June 2026;
- `revenue_usd` is non-empty;
- the customer exists in `customers.csv`;
- the product exists in the SQLite `product_catalog` table.

Join `events.csv` to `customers.csv` by `customer_id`.
Join `events.csv` to `analytics.db:product_catalog` by `product_id`.
Exclude rows with missing customer or product matches.

For top-product ordering:

1. sort by revenue descending;
2. break ties by product name ascending.

`metrics.json` must include:

- `join_matched_event_count`
- `excluded_unmatched_event_count`
- `total_revenue_usd`
- `top_region_by_revenue`
- `top_products_by_revenue`
- `top_category_by_revenue`

Round currency values to two decimals. Break region ties alphabetically.

## Report Rules

`report.md` must include these headings in order:

- `# DATA-01 Case 003 Memo`
- `## Summary`
- `## Join Checks`
- `## Caveats`

The report must mention the join-matched count, excluded unmatched count, total revenue, top region, and the top product ordering.
Do not mention profit, margin, forecasts, or conversion rates.

## Chart Rules

`chart_spec.json` must describe top product revenue with deterministic data:

- title: `Case 003 Top Products by Revenue`
- x-axis: `product`
- y-axis: `revenue_usd`
- one series named `revenue_usd`
