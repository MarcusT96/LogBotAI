# Base image
FROM python:3.12

# Set working directory
WORKDIR /backend

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file and the rest of the application
COPY . .

# Set environment variable for port
ENV PORT=8000

# Start the application using app.py
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:${PORT}", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]