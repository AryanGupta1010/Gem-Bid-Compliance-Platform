FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY model_services/colpali/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY model_services/colpali/main.py /app/main.py
EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
