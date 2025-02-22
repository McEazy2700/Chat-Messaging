FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chmod +x includes/scripts/dev_shell.sh

EXPOSE 8090
