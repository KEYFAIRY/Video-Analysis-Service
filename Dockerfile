# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Instalar dependencias del sistema para compilar mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente
COPY . .

# Exponer el puerto interno
EXPOSE 8100

# Comando por defecto al iniciar el contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100", "--reload"]