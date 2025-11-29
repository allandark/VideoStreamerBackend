#!/bin/bash

gunicorn -w 4 -b ${FLASK_RUN_HOST}:${FLASK_RUN_PORT} --access-logfile - --error-logfile - --log-level debug --timeout 120 VideoStreamAPI.app:app