FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# python:slim has no curl; the compose healthcheck uses python urllib instead
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
