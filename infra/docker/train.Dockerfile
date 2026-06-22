FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir poetry==1.8.3

COPY services/forecast/pyproject.toml services/forecast/poetry.lock* /workspace/services/forecast/
WORKDIR /workspace/services/forecast
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/forecast /workspace/services/forecast
COPY ethogram /workspace/ethogram
COPY core /workspace/core
COPY infra/configs /workspace/infra/configs

ENV AARFLINGO_CONFIG=/workspace/infra/configs/default.yaml

ENTRYPOINT ["python", "-m", "app.cli", "train"]
