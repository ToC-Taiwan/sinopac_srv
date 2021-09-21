FROM python:3.7.11-bullseye
USER root

ENV TZ=Asia/Taipei
ENV DEPLOYMENT=docker

ARG PYPORT
ARG GOLANGPORT
ARG TRADEID
ARG TRADEPASS
ARG CAPASS

WORKDIR /
RUN mkdir sinopac_srv
WORKDIR /sinopac_srv
COPY . .

RUN apt update -y && \
    apt install -y tzdata && \
    wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key && \
    apt-key add mosquitto-repo.gpg.key && \
    wget http://repo.mosquitto.org/debian/mosquitto-jessie.list -O /etc/apt/sources.list.d/mosquitto-jessie.list && \
    wget http://repo.mosquitto.org/debian/mosquitto-stretch.list -O /etc/apt/sources.list.d/mosquitto-stretch.list && \
    wget http://repo.mosquitto.org/debian/mosquitto-buster.list -O /etc/apt/sources.list.d/mosquitto-buster.list && \
    apt update && \
    apt install -y mosquitto && \
    apt autoremove -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-warn-script-location --no-cache-dir -r requirements.txt

ENTRYPOINT ["/sinopac_srv/scripts/docker-entrypoint.sh"]
