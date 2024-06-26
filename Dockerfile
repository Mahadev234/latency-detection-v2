FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean

EXPOSE 8080
CMD ["python", "app.py"]
