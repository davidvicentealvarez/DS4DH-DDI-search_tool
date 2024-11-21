#!/bin/bash
gunicorn --worker-tmp-dir /dev/shm --log-file -  -c /app/src/wsgi.py -b 0.0.0.0:8901 wsgi:app --preload