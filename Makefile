.PHONY: setup test smoke dev runtime studio electron train verify mobile-android mobile-verify

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
	PYTHONPATH=. poetry run pytest -q core/tests
	PYTHONPATH=.:services/ingest poetry run pytest -q services/ingest/tests
	PYTHONPATH=.:services/perception poetry run pytest -q services/perception/tests
	PYTHONPATH=.:services/forecast poetry run pytest -q services/forecast/tests
	PYTHONPATH=.:services/feedback poetry run pytest -q services/feedback/tests
	PYTHONPATH=.:services/runtime poetry run pytest -q services/runtime/tests
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

mobile-android:
	./scripts/mobile/setup-android-wsl.sh

mobile-verify:
	./scripts/mobile/verify-mobile.sh
