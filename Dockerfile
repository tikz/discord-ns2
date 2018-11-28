FROM python:3.6-alpine

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN apk add --update alpine-sdk freetype-dev openssl-dev

RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8001
ENTRYPOINT ["python", "main.py"]