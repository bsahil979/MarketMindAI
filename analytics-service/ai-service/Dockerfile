FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for ML models
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements with full AI dependencies
COPY ai-requirements.txt .
RUN pip install --no-cache-dir -r ai-requirements.txt

# Copy AI service code
COPY app/ai/ ./app/ai/
COPY app/ml/ ./app/ml/
COPY app/rag/ ./app/rag/
COPY app/llm/ ./app/llm/
COPY app/evaluation/ ./app/evaluation/
COPY app/database.py ./app/
COPY app/config.py ./app/

# Expose AI service port
EXPOSE 8001

# Run AI service
CMD ["uvicorn", "app.ai.ai_api:app", "--host", "0.0.0.0", "--port", "8001"]
