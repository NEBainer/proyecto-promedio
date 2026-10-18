FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo requirements: si no cambian, Docker reutiliza la capa cacheada
# y no reinstala todo en cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# No correr como root dentro del contenedor.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Render inyecta PORT; en local usa 8000.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
