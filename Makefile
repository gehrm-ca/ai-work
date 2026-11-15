.PHONY: demo demo-check test web-build

demo:
	bash scripts/run_demo.sh

test:
	python -m pytest -q

web-build:
	cd web && npm run build

demo-check: test web-build
	bash -n scripts/run_demo.sh
