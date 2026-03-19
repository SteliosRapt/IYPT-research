CASE ?= examples/default-case.json
CASE_DIR ?= examples/default-openfoam-case
VIEWER_DIR ?= examples/default-mock

.PHONY: web-dev web-build py-test case-export case-generate case-run viewer-data smoke examples

web-dev:
	npm run dev

web-build:
	npm run build

py-test:
	pytest

case-export:
	python3 -m services.geometry.cli export-case $(CASE) --output-dir examples/exported-geometry

case-generate:
	python3 -m services.orchestrator.cli generate-case $(CASE) --output-dir $(CASE_DIR)

case-run:
	python3 -m services.orchestrator.cli run-case $(CASE_DIR)

viewer-data:
	python3 -m services.viewer_data.cli mock-run $(CASE) --output-dir $(VIEWER_DIR)

examples:
	python3 scripts/build_examples.py

smoke:
	pytest
	python3 scripts/smoke_run.py
	npm run build

