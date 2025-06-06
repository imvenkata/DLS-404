# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy parent project files (needed for imports)
COPY ../ ./parent/

# Copy frontend application files
COPY . .

# Set Python path to include parent directory
ENV PYTHONPATH=/app/parent:$PYTHONPATH

# Create a non-root user for security
RUN useradd -m -u 1000 chainlit && chown -R chainlit:chainlit /app
USER chainlit

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the Chainlit application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"] 