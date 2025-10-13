FROM python:3.13-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p staticfiles media

# Exponer puerto
EXPOSE 8000

# Comando por defecto (puede ser sobrescrito en docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
