import docker
from flask import Flask, request
from multiprocessing import Process, Queue

# if we start the container running this file with the option
# -v /var/run/docker.sock:/var/run/socker.sock
# then this will be the same docker daemon as the host machine
client = docker.from_env()

# Basic flask server for putting new jobs into job queue
app = Flask(__name__)
logger = app.logger

# Build an image from a folder containing a dockerfile
def build_image(dockerfile_path):
    image = client.images.build(
            path = dockerfile_path, # path of dockerfile build context
            rm = True, # remove intermediary images
            pull = True) # pull newer version of FROM image, if possible
    return image

# Create a container from an image
def create_container(image):
    # TODO: make name of container meaningful
    container = client.containers.run(
            image = image.id, # image to start from
            #name = , # name of container
            volumes = {}, # volumes to bind (for output file access)
            detach = True, # run in background
            remove = True) # remove container once finished
    return container

def get_cbers_data(data_description):
    pass

def run_job(job_id, job_path):
    print("running job with job id " + str(job_id) + " and path " + str(job_path))
    return
    # TODO: implement
    image = build_image(job_path)
    container = create_container(image)
    
    container.start()

# This is run from a subprocess, so infinite loop is OK
def run_jobs(queue):
    while True:
        job_data = queue.get() # block until queue has item
        job_id = job_data["id"]
        job_path = job_data["path"]
        run_job(job_id, job_path)

# TODO: determine how to allow these to go through even if job is running.
#       flask is single-threaded, so new requests will wait until job is finished,
#       unless we do something about it.
@app.route("/", methods=["POST"])
def new_job():
    data = request.get_json()
    logger.debug("data:" + str(data))
    job_queue.put(data)
    return ('', 204) # Return "No content" but OK

# job queue manager thingy. this is crap code.
job_queue = Queue()
job_runner = Process(target = run_jobs, args = (job_queue,), daemon = True)
job_runner.start()
