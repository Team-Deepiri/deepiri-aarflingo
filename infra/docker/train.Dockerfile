FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock /workspace/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY services/forecast /workspace/services/forecast
COPY ethogram /workspace/ethogram
COPY core /workspace/core
COPY infra/configs /workspace/infra/configs
COPY aarflingo_cli /workspace/aarflingo_cli

RUN poetry install --no-interaction --no-ansi

ENV AARFLINGO_CONFIG=/workspace/infra/configs/default.yaml
ENV PYTHONPATH=/workspace:/workspace/services/forecast

ENTRYPOINT ["poetry", "run", "aarflingo-forecast", "train"]
