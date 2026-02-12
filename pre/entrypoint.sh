#!/bin/bash

# Use /app/ if main.ipynb exists there, otherwise fall back to the old directory
if [ -f /app/main.ipynb ]; then
    PIPELINE_DIR="/app"
else
    PIPELINE_DIR="/opt/pipelines"
    # Install extra deps from the old location if they exist
    if [ -f /opt/pipelines/extra-dependencies.txt ]; then
        pip install -r /opt/pipelines/extra-dependencies.txt
    fi
fi

cd "$PIPELINE_DIR"

export PYTHONPATH="$PIPELINE_DIR:${PYTHONPATH}"

bitswan-notebook "$PIPELINE_DIR/main.ipynb" -c "$PIPELINE_DIR/pipelines.conf"
