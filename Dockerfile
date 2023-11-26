FROM python:3.9.15

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements /app/requirements
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements-dev.txt

ADD . /app
WORKDIR /app
