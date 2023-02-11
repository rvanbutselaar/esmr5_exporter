FROM python:3.10.10-slim-buster

# Inspired by:
# https://github.com/prometheus/client_python
# https://github.com/gejanssen/slimmemeter-rpi

RUN pip3 install --upgrade --no-cache \
        prometheus_client \
        smeterd && \
        apt-get update && \
        apt-get upgrade -y && \
        rm -rf /var/lib/apt/lists/*

EXPOSE 8000

COPY  main.py /main.py
ENTRYPOINT ["/usr/local/bin/python3", "-u", "/main.py"]
