FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYGAME_HIDE_SUPPORT_PROMPT="hide"

# Install system dependencies for pygame (audio)
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-mixer-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright chromium (though the base image has it, this ensures version match)
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the server
CMD ["python", "app/main.py"]
