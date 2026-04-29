FROM python:3.9-slim

# FFmpeg install karne ke liye
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Server chalane ki command
CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
