FROM python:3.6.12

ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt
