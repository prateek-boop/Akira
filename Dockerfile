# Use a lightweight Python base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for FAISS and Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    chromium \
    chromium-driver \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# Using the CPU-only PyTorch index to keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV INDEX_DIR=/app/index_store
ENV LOG_LEVEL=INFO

# Create the index_store directory to ensure permissions are correct
RUN mkdir -p /app/index_store

# Expose the API port
EXPOSE 8000

# Command to run the Akira FastAPI Server
CMD ["python", "akira_api.py"]
