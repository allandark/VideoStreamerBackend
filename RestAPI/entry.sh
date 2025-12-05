#!/bin/bash

gunicorn -w ${N_CONCURRENT_WORKERS} -b ${FLASK_RUN_HOST}:${FLASK_RUN_PORT} --access-logfile - --error-logfile - --timeout 120 VideoStreamAPI.app:app