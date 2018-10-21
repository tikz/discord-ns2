FROM python:3.6-alpine

COPY . /app
COPY config_prod.py config.py
WORKDIR /app

RUN apk add --update alpine-sdk freetype-dev libpng-dev libffi-dev openssl-dev openblas-dev

# matplotlib: libpng-dev libffi-dev
# cryptography: openssl-dev
# numpy: openblas-dev

RUN pip install -r requirements.txt
CMD ["python", "main.py"]