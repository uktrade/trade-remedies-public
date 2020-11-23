FROM python:3.6.12
ENV DOCKERIZE_VERSION v0.6.1

ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt

# Install dockerize
RUN \
  wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz
