FROM python:3.7.12-bullseye
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
    apt autoremove -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-warn-script-location --no-cache-dir -r requirements.txt

ENTRYPOINT ["/sinopac_srv/scripts/docker-entrypoint.sh"]
