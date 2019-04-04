#!/bin/bash

source .env/bin/activate

export FLASK_APP=app/frontend.py
export FLASK_ENV=development

flask run
