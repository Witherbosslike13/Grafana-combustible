FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY collector.py .
COPY republicar_mqtt.py .
COPY datos_api.json .

CMD ["python", "-u", "collector.py"]
