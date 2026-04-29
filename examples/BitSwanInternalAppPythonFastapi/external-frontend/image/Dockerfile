FROM node:20-alpine

RUN npm install -g serve

# package.json lives in image/ so an edit to it bumps the image content
# hash and triggers a rebuild on next live-dev start. node_modules is
# installed once at build time and lives in /deps; the source tree (bind-
# mounted at /app) carries committed symlinks `package.json` and
# `node_modules` that point into /deps so Vite resolves modules correctly.
WORKDIR /deps
COPY package.json ./
RUN npm install

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
