FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/aarflingo
COPY pyproject.toml poetry.lock /opt/aarflingo/
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi -E yolo --no-root

COPY . /opt/aarflingo
RUN poetry install --no-interaction --no-ansi -E yolo

ENV PYTHONPATH=/opt/aarflingo:/opt/aarflingo/services/runtime
EXPOSE 8765
CMD ["poetry", "run", "aarflingo-runtime", "--host", "0.0.0.0", "--port", "8765"]
