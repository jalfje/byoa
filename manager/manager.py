import docker
import time
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
def build_image(image_name, dockerfile_path):
    image, logs = client.images.build(
            path = dockerfile_path, # path of dockerfile build context
            tag = image_name,
            rm = True, # remove intermediary images
            pull = True) # pull newer version of FROM image, if possible
    return image

# Create a container from an image
def create_container(image):
    logger.debug("Creating container from image with id %s", image.id)
    # TODO: make name of container meaningful somehow
    # TODO: add /output volume, pointing to job folder
    container = client.containers.create(
            image = image.id, # image to start from
            #name = , # name of container
            volumes = {}, # volumes to bind (for output file access)
            detach = True) # run in background
    return container

# TODO: stream container logs to debug output
def run_job(job_id, job_path):
    logger.debug("Running job with job id %s and path %s", str(job_id), str(job_path))
    # TODO: stream build logs to debug output
    image = build_image(job_id, job_path)
    logger.debug("Built image with id %s", str(image.id))
    container = create_container(image)
    logger.debug("Created container with name %s", str(container.name))
    container.start()
    logger.debug("Started container with name %s", str(container.name))
    # TODO: fill in here with 1) getting CBERS data, and 2) running data on script.
    #       also manage multiple containers; in this case pull this into function
    logger.debug("Container finished executing. Stopping container.")
    container.stop()
    logger.debug("Container stopped. Removing container.")
    container.remove()
    logger.debug("Container removed. Removing image.")
    client.images.remove(image.id)
    logger.debug("Image removed. Next job available.")
    return

# This is run from a subprocess, so infinite loop is OK
def run_jobs(queue):
    logger.debug("Running run_jobs!")
    while True:
        job_data = queue.get() # block until queue has item
        logger.debug("Got new job! Job data: %s", job_data)
        job_id = job_data["id"]
        job_path = job_data["path"]
        run_job(job_id, job_path)

# TODO: consider changing interface of input: at present, we accept a json
# with the job id and the job path - however, because this script is run in
# a different docker container to the sender, the job path is not necessarily
# valid, and only works if both the sender and this container use the same volume
# and path for jobs.
# Instead, we might want to just accept the job id, assume that the jobs files
# are in a folder labelled with that job id.
# Or, instead, actually pass the input files, and have this container save them.
# But that wouldn't really scale - having the frontend container save the files
# and then having them both accessible would be valid, because with something like
# AWS, they would be accessible to both containers with the same path.
@app.route("/", methods=["POST"])
def new_job():
    data = request.get_json()
    job_queue.put(data) # global job queue
    logger.debug("Put data into queue: %s", str(data))
    return ('', 204) # Return "No content", because we have nothing to give back.

# Job queue manager. This would ideally be put into a separate docker container,
# but that would have taken too much effort to implement correctly in our
# limited time frame. Instead, we simply start another thread for running jobs,
# and leave the main thread available for the flask endpoint to accept jobs and
# put them on the queue.
job_queue = Queue()
job_runner = Process(target = run_jobs, args = (job_queue,), daemon = True)
job_runner.start()
