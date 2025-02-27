FROM python:3.9-alpine

# Set working directory
WORKDIR /app

# Set timezone and environment variables
ENV TZ=Asia/Tehran
ENV PYTHONIOENCODING=utf8
ENV LANG=C.UTF-8
ENV FLASK_APP=run.py
ENV FLASK_DEBUG=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apk add --no-cache \
    tzdata \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p uploads && chmod 777 uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "-u", "run.py"] 