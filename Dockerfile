FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/app/ ./backend/app/

# Copy the frontend static files
COPY frontend/static/ ./frontend/static/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "backend.app.main"]
