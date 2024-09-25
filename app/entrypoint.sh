#!/bin/bash

# App entrypoint using debugpy
pip install debugpy -t /tmp && python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 main.py reload;

exec "$@"