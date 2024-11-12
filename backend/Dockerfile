# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variable for port
ENV PORT=8000

# Start the application with Gunicorn and Uvicorn workers
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"] 