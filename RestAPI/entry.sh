#!/bin/bash

gunicorn -w 4 -b ${FLASK_RUN_HOST}:${FLASK_RUN_PORT} --access-logfile - VideoStreamAPI.app:app