#!/bin/bash

# To setup the environment for running the contents of this repository, ensure the python3 and python3-venv packages are installed, then execute this file.

python3 -m venv ./.env && source .env/bin/activate && pip install -r requirements.txt
