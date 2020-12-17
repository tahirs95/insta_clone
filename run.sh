#!/usr/bin/env bash

export FLASK_APP=main.py
set -e
flask db init
flask db migrate
flask db upgrade