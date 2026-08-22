.PHONY: setup test smoke dev runtime studio electron train verify mobile-android mobile-verify web home-capture home-train kicad kicad-sch firmware firmware-test flash-collar

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

kicad:
	./kicad-launcher --run collar

kicad-sch:
	./kicad-launcher --sch verify

firmware-test:
	python3 -m pytest -q firmware/collar/test

firmware:
	python3 -m pytest -q firmware/collar/test
	cd firmware/collar && platformio run

flash-collar:
	./scripts/flash_collar.sh

test:
	python3 core/metrics/test_anticipate.py
	python3 -m pytest -q scripts/aarf_sch
	python3 -m pytest -q firmware/collar/test
	PYTHONPATH=. poetry run pytest -q core/tests
	PYTHONPATH=.:services/ingest poetry run pytest -q services/ingest/tests
	PYTHONPATH=.:services/perception poetry run pytest -q services/perception/tests
	PYTHONPATH=.:services/audio poetry run pytest -q services/audio/tests
	PYTHONPATH=.:services/voice poetry run pytest -q services/voice/tests
	PYTHONPATH=.:services/forecast poetry run pytest -q services/forecast/tests
	PYTHONPATH=.:services/feedback poetry run pytest -q services/feedback/tests
	PYTHONPATH=.:services/runtime poetry run pytest -q services/runtime/tests
	cd lib/aarf-gate && npm test

smoke:
	./scripts/smoke_pipeline.sh

dev:
	./scripts/dev.sh

home-capture:
	./scripts/home_capture.sh

home-train:
	PYTHONPATH=.:services/perception poetry run aarflingo-perception prep-dog-yolo
	PYTHONPATH=.:services/perception poetry run aarflingo-perception finetune-dog-yolo

runtime:
	./scripts/run_runtime.sh

web:
	./scripts/serve_web.sh

studio:
	cd apps/aarf-studio && npm run dev

electron:
	cd apps/aarf-studio && npm run electron:dev

mobile-android:
	./scripts/mobile/setup-android-wsl.sh

mobile-verify:
	./scripts/mobile/verify-mobile.sh
