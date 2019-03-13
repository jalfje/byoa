
# Overview

This repository is the front-end for our BYOA project that is a prototype of a hypothetical larger-scale system which would provide a simple method for a scientist to use the STAC-specified data in the Earth Data Store as input for their algorithms, and have their algorithms run on an automatically-scaling cloud service.

## Disclaimer

Our prof (Yvonne Coady) requested that our repository be made public. In the event that this repository is used by others in a manner that consitutes plagiarism, we accept no responsibility.

# Requirements

You will need the following packages to run the project: 

* python3
* python3-venv
* python3-pip

# Setup

With the requirements installed, execute the `setup.sh` script to set up your virtual environment and install packages into it with:

```
bash setup.sh
```

or 

```
chmod u+x setup.sh
./setup.sh
```

Then, activate the virtual environment with:

```
source .env/bin/activate
```

Finally, start the server with:

```
python3 app/main.py
```

A localhost port (default port 5000) to access the server will be printed to the console. Use this to access your server for as long as the process is running in the console.

