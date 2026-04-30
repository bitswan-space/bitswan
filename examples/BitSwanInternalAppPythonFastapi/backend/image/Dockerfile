FROM python:3.12-slim

ENV PYTHONPYCACHEPREFIX=/tmp/pycache

WORKDIR /deps

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
