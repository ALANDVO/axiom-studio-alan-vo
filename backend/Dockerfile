FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /app/data && chown -R appuser:appuser /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

COPY app /app/app

USER appuser

EXPOSE 8000
ENV PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
