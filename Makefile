PYTHON ?= python3
PYTHONPATH ?= src

.PHONY: validate list smoke compare-smoke if01-smoke data01-smoke doc01-smoke leak-check test

validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli validate

list:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli list-tasks

smoke:
	$(PYTHON) scripts/create_sample_artifacts.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task IF-01 --case case_001 --artifacts examples/artifacts/IF-01/case_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DATA-01 --case case_001 --artifacts examples/artifacts/DATA-01/case_001

compare-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/create_sample_runs.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli compare --baseline runs/baseline --candidate runs/spec_first --out reports/generated/compare_baseline_vs_spec_first.md --csv reports/generated/compare_baseline_vs_spec_first.csv

if01-smoke:
	$(PYTHON) scripts/create_sample_artifacts.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task IF-01 --case case_001 --artifacts examples/artifacts/IF-01/case_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task IF-01 --case case_002 --artifacts examples/artifacts/IF-01/case_002
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task IF-01 --case case_003 --artifacts examples/artifacts/IF-01/case_003
	$(PYTHON) scripts/create_if01_mutation.py --out artifacts/if01_mutations/case_mutation_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q tests/test_if01.py

data01-smoke:
	$(PYTHON) scripts/create_sample_artifacts.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DATA-01 --case case_001 --artifacts examples/artifacts/DATA-01/case_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DATA-01 --case case_002 --artifacts examples/artifacts/DATA-01/case_002
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DATA-01 --case case_003 --artifacts examples/artifacts/DATA-01/case_003
	$(PYTHON) scripts/create_data01_mutation.py --out artifacts/mutations/DATA-01/case_mutation_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q tests/test_data01.py

doc01-smoke:
	$(PYTHON) scripts/create_sample_artifacts.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DOC-01 --case case_001 --artifacts examples/artifacts/DOC-01/case_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DOC-01 --case case_002 --artifacts examples/artifacts/DOC-01/case_002
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DOC-01 --case case_003 --artifacts examples/artifacts/DOC-01/case_003
	$(PYTHON) scripts/create_doc01_mutation.py --out artifacts/mutations/DOC-01/case_mutation_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q tests/test_doc01.py

leak-check:
	$(PYTHON) scripts/public_leak_check.py .

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q
