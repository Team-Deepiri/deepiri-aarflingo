# Jetson / ARM64 home hub (Orin Nano class). Not the ESP32 collar.
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

WORKDIR /opt/aarflingo
COPY . /opt/aarflingo

RUN pip install --no-cache-dir onnxruntime opencv-python-headless fastapi uvicorn typer pyyaml numpy

ENV PYTHONPATH=/opt/aarflingo:/opt/aarflingo/services/edge-runtime:/opt/aarflingo/services/perception:/opt/aarflingo/services/forecast
ENV AARF_CAMERA=0

WORKDIR /opt/aarflingo/services/edge-runtime

# status = no camera. run = hub loop (USB/MIPI cam + optional collar BLE on the host).
CMD ["python3", "-m", "app.cli", "run", "--camera", "0"]
