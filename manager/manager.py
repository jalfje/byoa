import docker
import time
import os
import os.path as path
import shutil
import json
from flask import Flask, request
from multiprocessing import Process, Queue
from data_access import get_data_from_cbers

# We start the container running this file with the option
# -v /var/run/docker.sock:/var/run/socker.sock
# Which means that this will be the same docker daemon as the host machine
client = docker.from_env()
# Low-level client interface, equivalent to from_env() but with more control.
# We need this to stream image build output.
llclient = docker.APIClient(base_url='unix://var/run/docker.sock')

# Basic flask server for putting new jobs into job queue
app = Flask(__name__)
logger = app.logger

# Simple string formatting function
def node_str(node_idx):
    return "node_%02d" % (node_idx)

# Build an image from a folder containing a dockerfile
def build_image(image_tag, dockerfile_path):
    #image, logs = client.images.build(
    #        path = dockerfile_path, # path of dockerfile build context
    #        tag = image_name,
    #        rm = True, # remove intermediary images
    #        pull = True) # pull newer version of FROM image, if possible
    build_output = llclient.build(
                                    decode = True,
                                    path = dockerfile_path,
                                    tag = image_tag,
                                    rm = True,
                                    pull = True
                                 )

    for chunk in build_output:
        if 'stream' in chunk:
            for line in chunk['stream'].splitlines():
                logger.debug(line)
                if "Successfully built " in line:
                    logger.debug("Successful build!")
                    image_id = line[19:]
                    image = client.images.get(image_id)

    return image

# Create and run a container from an image
def run_container(image, job_id, node_idx, input_volume, output_volume):
    logger.debug("Running container from image with id %s", image.id)
    container = client.containers.run(
            image = image.id, # image to start from
            name = str(job_id) + node_str(node_idx), # name of container
            # bound volumes for input and output file access
            volumes = {input_volume: {"bind": "/input", "mode": "rw"},
                       output_volume: {"bind": "/output", "mode": "rw"}},
            detach = True, # run in background
            auto_remove = True # remove when finished
            )
    return container

# Creates a number of containers equal to the number of nodes specified
def run_all_containers(image, job_id, job_path, num_nodes):
    for node_idx in range(num_nodes):
        input_dir = path.join(job_path, node_str(node_idx), "input")
        output_dir = path.join(job_path, node_str(node_idx), "output")
        # Create and run detached container
        run_container(image, job_id, node_idx, input_dir, output_dir)

# Create folders to attach as volumes to running containers
def create_container_input_folders(job_path, num_nodes):
    for node_idx in range(num_nodes):
        # Determine directory names
        node_dir = path.join(job_path, node_str(node_idx))
        input_dir = path.join(node_dir, "input")
        output_dir = path.join(node_dir, "output")
        # Create I/O directories
        os.mkdir(node_dir)
        os.mkdir(input_dir)
        os.mkdir(output_dir)
        os.mkdir(path.join(input_dir, "images"))
        os.mkdir(path.join(input_dir, "metadata"))

# Put downloaded image and metadata files into folders, evenly split between
# all containers. This is done with a round-robin method
def arrange_input_files(photos_path, metadata_path, job_path, num_nodes):
    # Photo and associated metadata file have the same base filename; sorting
    # will ensure that their indices match up
    photo_files = sorted(os.listdir(photos_path))
    metadata_files = sorted(os.listdir(metadata_path))

    # Round-robin insert photos into node folders
    num_images = len(photo_files)
    node_idx = 0
    for x in range(num_images):
        input_dir = path.join(job_path, node_str(node_idx), "input")
        container_photos_dir = path.join(input_dir, "images")
        container_metadata_dir = path.join(input_dir, "metadata")
        shutil.move(path.join(photos_path, photo_files[x]),
                    path.join(container_photos_dir, photo_files[x]))
        shutil.move(path.join(metadata_path, metadata_files[x]),
                    path.join(container_metadata_dir, metadata_files[x]))
        node_idx = (node_idx + 1) % num_nodes

    # Delete now-empty download directories
    os.rmdir(photos_path)
    os.rmdir(metadata_path)

# TODO: stream image build logs to debug output
# TODO: remove images when job is finished
def run_job(job_id, num_nodes):
    logger.debug("Running job %s", str(job_id))

    # Job input files and data are stored in this path
    job_path = path.abspath(path.join(os.environ["JOBS_FOLDER"], job_id))
    photos_path = path.join(job_path, "images")
    metadata_path = path.join(job_path, "metadata")
    os.makedirs(photos_path, exist_ok = True)
    os.makedirs(metadata_path, exist_ok = True)

    logger.debug("Job path: %s", str(job_path))

    # files will be length 3
    files = [f for f in os.listdir(job_path) if path.isfile(path.join(job_path, f))]
    logger.debug("Files in job path: %s", str(files))
    for f in files:
        if f.endswith(".py"):
            script_file = path.join(job_path, f)
        if f.lower() == "dockerfile":
            dockerfile = path.join(job_path, f)
        if f.endswith(".json"):
            json_file = path.join(job_path, f)

    logger.debug("Script file: %s", script_file)
    logger.debug("Dockerfile: %s", dockerfile)
    logger.debug("Data description file: %s", json_file)
    logger.debug("Loading data description...")

    # Get input lat/lon bounding box and time range
    with open(json_file, 'r') as datadesc:
        json_data = json.load(datadesc)
        bounding_box = json_data["bbox"]
        time_range = json_data["time"]

    logger.debug("Data description loaded.")
    logger.debug("Bounding box: %s", str(bounding_box))
    logger.debug("Time range: %s", str(time_range))
    logger.debug("Starting process to download data in background...")

    # Get CBERS data on separate process, because it will take some time
    cbers_process = Process(target = get_data_from_cbers, args = (photos_path, metadata_path, bounding_box, time_range, num_nodes * 3))
    cbers_process.start()

    logger.debug("Started downloading data.")
    logger.debug("Appending COPY input script and CMD python to Dockerfile...")

    # Copy input script to python CMD ["python", "script.py"] to end of dockerfile
    with open(dockerfile, 'a') as dockerfile_obj:
        script_filename = path.basename(script_file)
        dockerfile_obj.write('\nCOPY ' + script_filename + ' /')
        dockerfile_obj.write('\nRUN mv /' + script_filename + ' /input_script.py')
        dockerfile_obj.write('\nCMD ["python", "/input_script.py"]')

    logger.debug("Dockerfile modified.")
    logger.debug("Building image...")

    # Build the provided dockerfile
    image = build_image(job_id, job_path)

    logger.debug("Image built.")
    logger.debug("Creating host-machine folders for container I/O volumes...")

    # Create I/O folders on host machine for containers
    create_container_input_folders(job_path, num_nodes)

    logger.debug("Created I/O volumes.")
    logger.debug("Waiting for data to finish downloading...")

    # Wait for CBERS data to all be downloaded, if it isn't already
    cbers_process.join()

    logger.debug("Data finished downloading.")
    logger.debug("Arranging input files into node folders...")

    # Sort the downloaded input files into the subfolders for each container
    arrange_input_files(photos_path, metadata_path, job_path, num_nodes)

    logger.debug("Input files arranged.")
    logger.debug("Creating and running containers in background...")

    # Run all containers
    run_all_containers(image, job_id, job_path, num_nodes)

    logger.debug("All containers running.")
    logger.debug("Job %s complete. Manager ready for next job.", job_id)

    return

# Infinite loop which gets jobs off of the job queue and starts them
def run_jobs(queue):
    logger.debug("Running run_jobs!")
    while True:
        job_data = queue.get() # block until queue has item
        logger.debug("Got new job! Job data: %s", job_data)
        job_id = job_data["id"]
        num_nodes = job_data["num_nodes"]
        run_job(job_id, num_nodes)

# The endpoint which the frontend sends requests to, which then adds them to
# the queue for processing. Ideally this would be done in two parts with a third
# container or other queue service, but that was beyond the feasible scope of
# our project.
@app.route("/", methods=["POST"])
def new_job():
    data = request.get_json()
    job_queue.put(data) # global job queue
    logger.debug("Put data into queue: %s", str(data))
    # Return "204 No Content", because we have no data to return.
    return ('', 204)

# Job queue manager. This would ideally be put into a separate docker container,
# but that would have taken too much effort to implement correctly in our
# limited time frame. Instead, we simply start another thread for running jobs,
# and leave the main thread available for the flask endpoint to accept jobs and
# put them on the queue.
job_queue = Queue()
job_runner = Process(target = run_jobs, args = (job_queue,))
job_runner.start()
