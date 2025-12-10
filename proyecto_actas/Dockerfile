# Imagen base
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema: tesseract, poppler, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# 🔹 OJO: el archivo está en proyecto_actas/requirements.txt
COPY proyecto_actas/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el código de la carpeta proyecto_actas
COPY proyecto_actas/ ./

# Puerto (Render pone la variable PORT)
ENV PORT=10000

# Comando de inicio
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
