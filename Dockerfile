FROM python:3.10.15

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /app/
COPY requirements-dev.txt /app/

WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements-dev.txt


ADD . /app
WORKDIR /app