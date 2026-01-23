FROM node:20-alpine

# Install serve globally
RUN npm install -g serve

# Install dependencies to /deps (cached layer, survives mount)
WORKDIR /deps
COPY package.json ./
RUN npm install

# App source will be mounted here at runtime
WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
