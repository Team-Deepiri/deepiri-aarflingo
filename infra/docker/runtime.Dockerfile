FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/aarflingo
COPY . /opt/aarflingo

RUN pip install --no-cache-dir poetry \
    && cd services/runtime && poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && cd ../forecast && poetry config virtualenvs.create false && poetry install --no-interaction \
    && cd ../perception && poetry config virtualenvs.create false && poetry install --no-interaction \
    && cd ../feedback && poetry config virtualenvs.create false && poetry install --no-interaction

ENV PYTHONPATH=/opt/aarflingo
EXPOSE 8765
CMD ["python", "-m", "app.cli", "serve", "--host", "0.0.0.0", "--port", "8765"]
