
# Overview

This repository is the front-end for our BYOA project that is a prototype of a hypothetical larger-scale system which would provide a simple method for a scientist to use the STAC-specified data in the Earth Data Store as input for their algorithms, and have their algorithms run on an automatically-scaling cloud service.

## Disclaimer

Our prof (Yvonne Coady) requested that our repository be made public. In the event that this repository is used by others in a manner that consitutes plagiarism, we accept no responsibility.

# Requirements

You will need the following packages to run the project: 

* docker
* docker-compose

# Setup

With the requirements installed, simply run 

```
docker-compose up -d
```

from within the main folder. This will build both the frontend and manager docker images, create a container for each, get them to talk to each other, and allow them to be accessed from your host machine.

A localhost port (port 8000) to access the server will be printed to the console. Use this to access your server for as long as the process is running in the console. The main endpoint is `/submit/` (and the endpoint `/` redirects to `/submit/`), which allows you to upload a python script, a dockerfile, and a json description of the data you wish to run the script on.

# Teardown

To stop the running containers, simply run

```
docker-compose down
```

Again from within the main folder.
