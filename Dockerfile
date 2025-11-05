# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Install PyTorch CPU-only first (much smaller and faster)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Instalar resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLO model to avoid runtime download issues
RUN python -c "from ultralytics import YOLO; YOLO('yolo11m-pose.pt')"

# Copiar todo el código fuente
COPY . .

# Comando por defecto al iniciar el contenedor
CMD ["python", "-m", "app.main"]