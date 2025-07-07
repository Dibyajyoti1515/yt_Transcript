FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install git (needed to install whisper from GitHub)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install yt-dlp
RUN pip install yt-dlp

# Copy requirements (that includes flask, waitress, whisper from GitHub)
COPY requirements.txt .

# Install python dependencies
RUN pip install -r requirements.txt

# Copy all your code, including the ffmpeg folder manually added in your repo
COPY . .

# Expose the flask port
EXPOSE 5000

# Run your main app
CMD ["python", "main.py"]
