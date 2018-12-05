FROM python:3.6-alpine

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN apk add --update alpine-sdk libffi-dev openssl-dev

RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8001

LABEL "com.centurylinklabs.watchtower.enable"="true"
ENTRYPOINT ["python", "main.py"]