PYTHON ?= python3
PYTHONPATH ?= src

.PHONY: validate list smoke leak-check test

validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli validate

list:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli list-tasks

smoke:
	$(PYTHON) scripts/create_sample_artifacts.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task IF-01 --case case_001 --artifacts examples/artifacts/IF-01/case_001
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m agent_bench_lab.cli score --task DATA-01 --case case_001 --artifacts examples/artifacts/DATA-01/case_001

leak-check:
	$(PYTHON) scripts/public_leak_check.py .

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q
