.PHONY: setup test smoke dev runtime studio electron train verify

setup:
	./setup.sh

setup-run:
	./setup.sh --run

train:
	./scripts/train_aarflingo.sh

verify:
	./scripts/verify_aarflingo.sh

branding:
	./scripts/sync-branding.sh

test:
	python3 core/metrics/test_anticipate.py
	PYTHONPATH=. python3 -m pytest -q core/tests
	cd services/ingest && PYTHONPATH=../..:$$PWD poetry run pytest -q
	cd services/perception && PYTHONPATH=../..:$$PWD poetry run pytest -q
	cd services/forecast && PYTHONPATH=../..:$$PWD poetry run pytest -q
	cd services/feedback && PYTHONPATH=../..:$$PWD poetry run pytest -q
	cd services/runtime && PYTHONPATH=../..:$$PWD poetry run pytest -q
	cd lib/aarf-gate && npm test

smoke:
	./scripts/smoke_pipeline.sh

dev:
	./scripts/dev.sh

runtime:
	./scripts/run_runtime.sh

studio:
	cd apps/aarf-studio && npm run dev

electron:
	cd apps/aarf-studio && npm run electron:dev
