# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp manually (latest version)
RUN pip install --upgrade pip
RUN pip install yt-dlp

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy your code
COPY . .

# Expose port (default Flask port)
EXPOSE 5000

# Run the application
CMD ["python", "yt_trimmer.py"]
