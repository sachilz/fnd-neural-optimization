FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary files for inference
COPY backend/ ./backend/
COPY src/ ./src/
COPY models/ ./models/
COPY data/processed/ ./data/processed/
COPY results/metrics/ ./results/metrics/

# Expose backend port
EXPOSE 8000

# Run uvicorn
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
