# syntax=docker/dockerfile:1

############################
# 1️⃣ Base Image
############################
FROM python:3.12-slim AS base

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

############################
# 2️⃣ System Dependencies
############################
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

############################
# 3️⃣ Install Python Dependencies
############################
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

############################
# 4️⃣ Create Non-Root User
############################
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

############################
# 5️⃣ Copy Application Code
############################
COPY . .

############################
# 6️⃣ Switch to Non-Root User
############################
USER appuser

############################
# 7️⃣ Expose Cloud Run Port
############################
EXPOSE 8080

############################
# 8️⃣ Production Server Command
############################
CMD ["uvicorn", "app.v1.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "2"]
