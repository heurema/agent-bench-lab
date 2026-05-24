from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "mutations" / "DATA-01" / "case_mutation_001"


SPEC = """# DATA-01 Generated Public-Style Mutation

Use the synthetic files under `data/`:

- `events.csv`
- `customers.csv`
- `analytics.db`

Produce exactly these artifacts and no others:

- `metrics.json`
- `report.md`
- `chart_spec.json`

Use paid purchase events inside July 2026 with non-empty revenue, matching customer ids, and matching products from `analytics.db:product_catalog`.
Join customers by `customer_id`, join products by `product_id`, normalize region names by trimming whitespace, and break ties alphabetically.

Report headings must be:

- `# DATA-01 Mutation Memo`
- `## Summary`
- `## Method`
- `## Caveats`

Do not mention profit, margin, forecasts, or conversion rates.
"""


CHECK_CONFIG = {
    "case_id": "case_mutation_001",
    "description": (
        "Generated public-style DATA-01 mutation with changed synthetic names, shifted dates, "
        "changed numeric values, reordered rows, and harmless distractors."
    ),
    "required_artifacts": ["metrics.json", "report.md", "chart_spec.json"],
    "allow_extra_files": False,
    "score_caps": {
        "missing_required_file": 0.0,
        "missing_metrics": 0.0,
        "invalid_metrics_json": 0.0,
        "invalid_chart_json": 0.75,
        "missing_metric": 0.65,
        "wrong_metric": 0.65,
        "forbidden_metric": 0.65,
        "missing_report_section": 0.8,
        "unsupported_metric": 0.7,
        "banned_phrase": 0.6,
        "missing_chart_series": 0.75,
        "wrong_chart_spec": 0.85,
        "extra_metric": 0.75,
        "extra_file": 0.8,
    },
    "metrics": {
        "allow_extra_keys": False,
        "forbidden_keys": [
            "profit_usd",
            "margin_pct",
            "forecast_revenue_usd",
            "conversion_rate",
        ],
        "required": {
            "qualified_event_count": {"expected": 3, "tolerance": 0},
            "total_revenue_usd": {"expected": 260.0, "tolerance": 0.01},
            "top_region_by_revenue": {"expected": "EMEA", "normalize_strings": True},
            "revenue_by_region": {
                "expected": {"AMER": 110.0, "EMEA": 150.0},
                "tolerance": 0.01,
            },
            "top_category_by_revenue": {"expected": "workspace", "normalize_strings": True},
        },
    },
    "report": {
        "required_sections": [
            "# DATA-01 Mutation Memo",
            "## Summary",
            "## Method",
            "## Caveats",
        ],
        "required_references": [
            {"metric": "qualified_event_count", "text": "Qualified events: 3"},
            {"metric": "total_revenue_usd", "text": "Total revenue: 260.00"},
            {"metric": "top_region_by_revenue", "text": "Top region: EMEA"},
            {"metric": "top_category_by_revenue", "text": "Top category: workspace"},
        ],
        "banned_phrases": ["I guessed", "not enough data"],
        "unsupported_metric_phrases": ["profit", "margin", "forecast", "conversion rate"],
        "max_words": 180,
    },
    "chart_spec": {
        "tolerance": 0.01,
        "expected": {
            "title": "Mutation Revenue by Region",
            "x_axis": "region",
            "y_axis": "revenue_usd",
            "series": [
                {
                    "name": "revenue_usd",
                    "points": [
                        {"label": "EMEA", "value": 150.0},
                        {"label": "AMER", "value": 110.0},
                    ],
                }
            ],
        },
    },
}


EVENT_ROWS = [
    ["M-4003", "MC-003", "MP-nimbus", "2026-07-04T08:00:00", "purchase", "paid", "60.00"],
    ["M-4001", "MC-001", "MP-nimbus", "2026-07-01T08:00:00", "purchase", "paid", "90.00"],
    ["M-4005", "MC-004", "MP-orion", "2026-07-05T08:00:00", "purchase", "pending", "999.00"],
    ["M-4002", "MC-002", "MP-orion", "2026-07-03T08:00:00", "purchase", "paid", "110.00"],
]

CUSTOMER_ROWS = [
    ["MC-001", " EMEA ", "team"],
    ["MC-002", "AMER", "enterprise"],
    ["MC-003", "EMEA", "team"],
    ["MC-004", "APAC", "trial"],
]

PRODUCT_ROWS = [
    ("MP-nimbus", "Nimbus Plan", "workspace"),
    ("MP-orion", "Orion Suite", "workspace"),
]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def write_analytics_db(path: Path) -> None:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE product_catalog ("
            "product_id TEXT PRIMARY KEY, "
            "product_name TEXT NOT NULL, "
            "category TEXT NOT NULL)"
        )
        connection.executemany("INSERT INTO product_catalog VALUES (?, ?, ?)", PRODUCT_ROWS)
        connection.commit()
    finally:
        connection.close()


def create_mutation(output_dir: Path) -> Path:
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "spec.md").write_text(SPEC, encoding="utf-8")
    (output_dir / "check_config.json").write_text(
        json.dumps(CHECK_CONFIG, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(
        data_dir / "events.csv",
        ["event_id", "customer_id", "product_id", "occurred_at", "event_type", "status", "revenue_usd"],
        EVENT_ROWS,
    )
    write_csv(data_dir / "customers.csv", ["customer_id", "region", "segment"], CUSTOMER_ROWS)
    write_analytics_db(data_dir / "analytics.db")
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a safe public-style DATA-01 mutation case")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output_dir = create_mutation(args.out)
    print(f"DATA-01 mutation case created at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
