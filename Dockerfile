# Dockerfile
FROM python:3.11


COPY src /src
WORKDIR /src

RUN pip install -r requirements.txt
