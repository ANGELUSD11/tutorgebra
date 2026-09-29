FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install minimal system dependencies if needed (for gTTS/fastapi mostly none are needed, but let's keep it safe)
# RUN apt-get update && apt-get install -y ...

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the server (Railway provides $PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
