FROM node:20-alpine

RUN npm install -g serve

WORKDIR /deps
COPY package.json ./
RUN npm install

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
