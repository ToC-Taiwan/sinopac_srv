# SINOPAC SRV

[![pipeline status](https://gitlab.tocraw.com/root/sinopac_srv/badges/main/pipeline.svg)](https://gitlab.tocraw.com/root/sinopac_srv/-/commits/main)
[![Maintained](https://img.shields.io/badge/Maintained-yes-green)](https://gitlab.tocraw.com/root/sinopac_srv)
[![Python](https://img.shields.io/badge/Python-3.7.11-yellow?logo=python&logoColor=yellow)](https://python.org)
[![OS](https://img.shields.io/badge/OS-Linux-orange?logo=linux&logoColor=orange)](https://www.linux.org/)
[![Container](https://img.shields.io/badge/Container-Docker-blue?logo=docker&logoColor=blue)](https://www.docker.com/)

## Features

### Transfer Sinopac Python API into Restful API

- [API Docs](http://sinopac-srv.tocraw.com:3333/apidocs)

### Initialize

```sh
pip freeze > requirements.txt
```

```sh
pip install --no-warn-script-location --no-cache-dir -r requirements.txt
mypy --install-types --non-interactive ./src/main.py
```

```sh
pip uninstall -y -r requirements.txt
```

### Git

```sh
git fetch --prune --prune-tags origin
git check-ignore *
```

### From Sino Original Pip

```sh
pip install \
    --no-warn-script-location \
    --no-cache-dir \
    requests shioaji Flask flasgger waitress \
    autopep8 protobuf mypy types-protobuf mypy-protobuf \
    pylint pylint-protobuf simplejson
```

## Authors

- [**Tim Hsu**](https://gitlab.tocraw.com/root)
