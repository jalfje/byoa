#!/bin/bash

source .env/bin/activate

export FLASK_APP=app/main.py
export FLASK_ENV=development

flask run
