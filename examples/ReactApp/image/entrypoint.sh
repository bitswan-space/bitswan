#!/bin/sh
set -e

ln -s /deps/node_modules /app/node_modules
ln -s /deps/package.json /app/package.json

npm run build
exec serve -s dist -l 8080
