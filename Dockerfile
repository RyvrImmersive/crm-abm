FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with explicit version pinning
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install pydantic 1.10.8 to ensure the correct version
RUN pip install --no-cache-dir pydantic==1.10.8

# Copy the rest of the application
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create environment file from template
RUN cp src/langflow/.env.template src/langflow/.env

# Set environment variables
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# Start the application
CMD ["uvicorn", "src.langflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
