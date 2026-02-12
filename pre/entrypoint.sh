#!/bin/bash
cd /app/

export PYTHONPATH="/app:${PYTHONPATH}"

bitswan-notebook /app/main.ipynb -c /app/pipelines.conf
