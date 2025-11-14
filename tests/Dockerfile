# Imagen base liviana
FROM python:3.10-slim

WORKDIR /app

# Dependencias mínimas de sistema para Python
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements de pruebas
COPY requirements.txt .

# Instalar dependencias solo para pruebas
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
# Copiar todo el código del proyecto
COPY .. /app

# Ejecutar pruebas por defecto
CMD ["pytest", "-v", "--tb=short"]
