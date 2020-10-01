FROM python:3.7

ADD . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt
RUN pip install /app/trade_remedies_client/trade-remedies-client-0.1.tar.gz