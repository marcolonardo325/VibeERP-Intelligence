FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + data files needed at runtime
COPY live_tube_server.py live_map.html vehicle_assets.json work_orders.json* ./

EXPOSE 8000

# 2 workers, 8 threads — enough for the 1Hz polling + background TfL refresh
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 8 --timeout 120 live_tube_server:app"]
