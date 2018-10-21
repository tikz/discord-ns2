FROM python:3.6-alpine

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN apk add --update alpine-sdk freetype-dev libpng-dev libffi-dev openssl-dev openblas-dev

# matplotlib: libpng-dev libffi-dev
# cryptography: openssl-dev
# numpy: openblas-dev

RUN pip install -r requirements.txt

COPY . /app
COPY config_prod.py /app/config.py
WORKDIR /app

CMD ["python", "main.py"]