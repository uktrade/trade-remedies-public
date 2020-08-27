FROM python:3.7

RUN apt-get update && apt-get install -y wget

WORKDIR /opt/traderemedies/public
ADD . /opt/traderemedies/public
VOLUME ["/opt/traderemedies/public"]

RUN pip install --no-cache-dir -r requirements-dev.txt && \
    pip install -U /opt/traderemedies/public/trade_remedies_client/trade-remedies-client-*


# Install dockerize https://github.com/jwilder/dockerize
ENV DOCKERIZE_VERSION v0.6.1
RUN wget -q https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz


EXPOSE 8002

ENTRYPOINT ./start.sh
