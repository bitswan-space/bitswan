FROM golang:1.22-alpine

RUN go install github.com/air-verse/air@latest

WORKDIR /deps
COPY go.mod go.sum ./
RUN go mod download

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
COPY air.toml /etc/air.toml
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
