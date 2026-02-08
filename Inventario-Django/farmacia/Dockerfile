# Usar una imagen base oficial de Python ligera
FROM python:3.13-slim

# Establecer variables de entorno para optimizar Python en Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el código del proyecto al contenedor
COPY . /app/

# Exponer el puerto donde correrá Gunicorn
EXPOSE 8000

# Comando por defecto para producción (Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "farmacia.wsgi:application"]