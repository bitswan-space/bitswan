FROM golang:1.23-alpine

RUN go install github.com/air-verse/air@v1.61.7

ENV GOFLAGS=-mod=mod

WORKDIR /deps
COPY go.mod ./
RUN go mod download

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
COPY air.toml /etc/air.toml
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
