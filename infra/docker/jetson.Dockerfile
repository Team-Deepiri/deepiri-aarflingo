# Jetson / ARM64 edge deployment (Orin Nano class)
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

WORKDIR /opt/aarflingo
COPY . /opt/aarflingo

RUN pip install --no-cache-dir onnxruntime opencv-python-headless fastapi uvicorn typer pyyaml numpy

ENV PYTHONPATH=/opt/aarflingo:/opt/aarflingo/services/perception:/opt/aarflingo/services/edge-runtime
ENV AARF_CAMERA=0

CMD ["python3", "-m", "app.cli", "run", "--camera", "0"]
