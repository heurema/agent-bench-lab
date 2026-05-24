import csv
import importlib.util
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from agent_bench_lab.scoring import score_task

REQUIRED_SCORE_FIELDS = {
    "run_id",
    "task_id",
    "case_id",
    "task_version",
    "scorer_version",
    "agent_config_id",
    "agent_config_hash",
    "success",
    "score",
    "pass_threshold",
    "components",
    "policy_violations",
    "errors",
    "artifact_hashes",
    "metadata",
}


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def data01_config(case_id: str) -> dict:
    config_path = root_dir() / "fixtures" / "public" / "DATA-01" / case_id / "check_config.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def expected_metrics(config: dict) -> dict:
    return {
        key: rule["expected"]
        for key, rule in config["metrics"]["required"].items()
    }


def data01_fixture_dir(case_id: str) -> Path:
    return root_dir() / "fixtures" / "public" / "DATA-01" / case_id


def load_products(case_id: str) -> dict[str, dict[str, str]]:
    db_path = data01_fixture_dir(case_id) / "data" / "analytics.db"
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT product_id, product_name, category FROM product_catalog"
        ).fetchall()
    return {
        product_id: {"product_name": product_name, "category": category}
        for product_id, product_name, category in rows
    }


def load_customers(case_id: str) -> dict[str, dict[str, str]]:
    path = data01_fixture_dir(case_id) / "data" / "customers.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["customer_id"]: row for row in rows}


def load_events(case_id: str) -> list[dict[str, str]]:
    path = data01_fixture_dir(case_id) / "data" / "events.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def public_metrics_from_fixtures(case_id: str) -> dict:
    customers = load_customers(case_id)
    products = load_products(case_id)
    events = load_events(case_id)
    window_start = "2026-06-01T00:00:00" if case_id == "case_003" else "2026-05-01T00:00:00"
    window_end = "2026-06-30T23:59:59" if case_id == "case_003" else "2026-05-31T23:59:59"
    seen_event_ids = set()
    duplicate_ids = []
    qualified = []
    null_revenue_count = 0
    unmatched_count = 0

    for row in events:
        if case_id == "case_002":
            if row["event_id"] in seen_event_ids:
                duplicate_ids.append(row["event_id"])
                continue
            seen_event_ids.add(row["event_id"])
        in_window = window_start <= row["occurred_at"] <= window_end
        eligible_status = row["event_type"] == "purchase" and row["status"] == "paid"
        if not (in_window and eligible_status):
            continue
        if not row["revenue_usd"]:
            null_revenue_count += 1
            continue
        customer = customers.get(row["customer_id"])
        product = products.get(row["product_id"])
        if customer is None or product is None:
            unmatched_count += 1
            continue
        qualified.append((row, customer, product))

    revenue_by_region = defaultdict(float)
    revenue_by_category = defaultdict(float)
    revenue_by_product = defaultdict(float)
    for row, customer, product in qualified:
        revenue = float(row["revenue_usd"])
        region = customer["region"].strip().upper()
        revenue_by_region[region] += revenue
        revenue_by_category[product["category"]] += revenue
        product_name = product["product_name"]
        revenue_by_product[product_name] += revenue

    top_region = sorted(revenue_by_region.items(), key=lambda item: (-item[1], item[0]))[0][0]
    top_category = sorted(revenue_by_category.items(), key=lambda item: (-item[1], item[0]))[0][0]
    total = round_money(sum(float(row["revenue_usd"]) for row, _, _ in qualified))
    normalized_region_revenue = {
        region: round_money(value)
        for region, value in sorted(revenue_by_region.items())
    }

    if case_id == "case_001":
        return {
            "qualified_event_count": len(qualified),
            "unique_customer_count": len({row["customer_id"] for row, _, _ in qualified}),
            "total_revenue_usd": total,
            "top_region_by_revenue": top_region,
            "revenue_by_region": normalized_region_revenue,
            "top_category_by_revenue": top_category,
        }
    if case_id == "case_002":
        boundary_count = sum(
            1
            for row, _, _ in qualified
            if row["occurred_at"] in {"2026-05-01T00:00:00", "2026-05-31T23:59:59"}
        )
        return {
            "qualified_event_count": len(qualified),
            "duplicate_event_ids_ignored": sorted(set(duplicate_ids)),
            "null_revenue_event_count": null_revenue_count,
            "boundary_event_count": boundary_count,
            "total_revenue_usd": total,
            "top_region_by_revenue": top_region,
            "revenue_by_region": normalized_region_revenue,
            "top_category_by_revenue": top_category,
        }

    top_products = [
        {"product": product_name, "revenue_usd": round_money(revenue)}
        for product_name, revenue in sorted(
            revenue_by_product.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    return {
        "join_matched_event_count": len(qualified),
        "excluded_unmatched_event_count": unmatched_count,
        "total_revenue_usd": total,
        "top_region_by_revenue": top_region,
        "top_products_by_revenue": top_products,
        "top_category_by_revenue": top_category,
    }


def report_text(config: dict, *, include_all_sections: bool = True, extra_line: str = "") -> str:
    sections = config["report"]["required_sections"]
    if not include_all_sections:
        sections = sections[:-1]
    lines = [
        sections[0],
        "",
        sections[1],
        *[f"- {item['text']}" for item in config["report"]["required_references"]],
    ]
    for section in sections[2:]:
        lines.extend(["", section, "- Applied the public synthetic fixture rules."])
    if extra_line:
        lines.extend(["", extra_line])
    return "\n".join(lines) + "\n"


def write_valid_artifacts(artifact_dir: Path, case_id: str) -> None:
    config = data01_config(case_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "metrics.json").write_text(
        json.dumps(expected_metrics(config), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "report.md").write_text(report_text(config), encoding="utf-8")
    (artifact_dir / "chart_spec.json").write_text(
        json.dumps(config["chart_spec"]["expected"], indent=2) + "\n",
        encoding="utf-8",
    )


def test_data01_valid_public_cases_pass(tmp_path):
    for case_id in ("case_001", "case_002", "case_003"):
        artifact_dir = tmp_path / case_id
        write_valid_artifacts(artifact_dir, case_id)

        result = score_task(root_dir(), "DATA-01", case_id, artifact_dir)

        assert result["success"], case_id
        assert result["score"] >= result["pass_threshold"], case_id
        assert REQUIRED_SCORE_FIELDS.issubset(result), case_id


def test_data01_public_expected_values_match_synthetic_fixtures():
    for case_id in ("case_001", "case_002", "case_003"):
        assert expected_metrics(data01_config(case_id)) == public_metrics_from_fixtures(case_id)


def test_data01_missing_metrics_json_fails(tmp_path):
    artifact_dir = tmp_path / "missing-metrics"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "metrics.json").unlink()

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert any("missing required file: metrics.json" in item for item in result["policy_violations"])


def test_data01_invalid_metrics_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-json"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "metrics.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert "invalid JSON: metrics.json" in result["policy_violations"]


def test_data01_wrong_numeric_metric_fails(tmp_path):
    artifact_dir = tmp_path / "wrong-metric"
    write_valid_artifacts(artifact_dir, "case_001")
    metrics = json.loads((artifact_dir / "metrics.json").read_text(encoding="utf-8"))
    metrics["total_revenue_usd"] = 999.99
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.65
    assert "metric mismatch: total_revenue_usd" in result["policy_violations"]


def test_data01_numeric_tolerance_allows_small_delta(tmp_path):
    artifact_dir = tmp_path / "tolerance"
    write_valid_artifacts(artifact_dir, "case_001")
    metrics = json.loads((artifact_dir / "metrics.json").read_text(encoding="utf-8"))
    metrics["total_revenue_usd"] = 820.509
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert result["success"]


def test_data01_missing_required_report_section_fails(tmp_path):
    artifact_dir = tmp_path / "missing-section"
    write_valid_artifacts(artifact_dir, "case_002")
    config = data01_config("case_002")
    (artifact_dir / "report.md").write_text(
        report_text(config, include_all_sections=False),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "DATA-01", "case_002", artifact_dir)

    assert not result["success"]
    assert any("missing or misordered report section" in item for item in result["policy_violations"])


def test_data01_unsupported_metric_is_detected(tmp_path):
    artifact_dir = tmp_path / "unsupported"
    write_valid_artifacts(artifact_dir, "case_001")
    config = data01_config("case_001")
    (artifact_dir / "report.md").write_text(
        report_text(config, extra_line="Profit increased by 10 percent."),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert any("unsupported report metrics" in item for item in result["policy_violations"])


def test_data01_banned_phrase_is_detected(tmp_path):
    artifact_dir = tmp_path / "banned"
    write_valid_artifacts(artifact_dir, "case_001")
    config = data01_config("case_001")
    (artifact_dir / "report.md").write_text(
        report_text(config, extra_line="I guessed one row."),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert any("banned report phrases" in item for item in result["policy_violations"])


def test_data01_extra_file_detection_works(tmp_path):
    artifact_dir = tmp_path / "extra"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "scratch.txt").write_text("extra output\n", encoding="utf-8")

    result = score_task(root_dir(), "DATA-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.8
    assert any("extra files" in item for item in result["policy_violations"])


def test_data01_chart_spec_validation_works(tmp_path):
    artifact_dir = tmp_path / "chart"
    write_valid_artifacts(artifact_dir, "case_003")
    chart_spec = json.loads((artifact_dir / "chart_spec.json").read_text(encoding="utf-8"))
    chart_spec["series"][0]["points"] = chart_spec["series"][0]["points"][:1]
    (artifact_dir / "chart_spec.json").write_text(json.dumps(chart_spec), encoding="utf-8")

    result = score_task(root_dir(), "DATA-01", "case_003", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.75
    assert any("chart spec mismatch: series" in item for item in result["policy_violations"])


def test_data01_mutation_script_creates_valid_case_structure(tmp_path):
    script_path = root_dir() / "scripts" / "create_data01_mutation.py"
    spec = importlib.util.spec_from_file_location("create_data01_mutation", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    output_dir = module.create_mutation(tmp_path / "mutation")

    assert (output_dir / "spec.md").exists()
    assert (output_dir / "data" / "events.csv").exists()
    assert (output_dir / "data" / "customers.csv").exists()
    config = json.loads((output_dir / "check_config.json").read_text(encoding="utf-8"))
    assert config["case_id"] == "case_mutation_001"
    assert config["required_artifacts"] == ["metrics.json", "report.md", "chart_spec.json"]
    with sqlite3.connect(output_dir / "data" / "analytics.db") as connection:
        product_count = connection.execute("SELECT COUNT(*) FROM product_catalog").fetchone()[0]
    assert product_count == 2
