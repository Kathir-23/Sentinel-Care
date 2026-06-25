#!/bin/bash
# Vercel build script — runs during deployment
pip install -r requirements.txt
python manage.py collectstatic --noinput
