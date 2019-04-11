import os
import logging
import requests
from uuid import uuid4
from flask import Flask, request, flash, redirect, send_from_directory, url_for, render_template


app = Flask(__name__)

# This is for some reason necessary for message flashing
app.secret_key = "super duper secret key!"

# 32 MB max upload size
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# Set up logging
logger = app.logger


# Save a file
def save_file(directory, file_obj):
    path = os.path.join(directory, file_obj.filename)
    file_obj.save(path)
    logger.debug("Saved file to %s", path)

# Get the job manager's URL
def get_job_manager_url():
    host = os.environ["MANAGER_HOST"]
    port = os.environ["MANAGER_PORT"]
    url = "http://" + host + ":" + port + "/"
    return url

# TODO: somehow (cookies?) save which files were chosen to upload and
#       put them back into the submit-file buttons.
@app.route("/submit/", methods=["GET", "POST"])
def submit_job():
    if request.method == "POST":
        # class of request.files is werkzeug.ImmutableMultiDict
        logger.debug("Job submitted with request files: %s", str(request.files))

        # Get our 3 files from the request
        script = request.files.get("script")
        dockerfile = request.files.get("dockerfile")
        datadesc = request.files.get("datadesc")
        logger.debug("Script file: " + str(script))
        logger.debug("Dockerfile: " + str(dockerfile))
        logger.debug("Data description file: " + str(datadesc))
        # Get # nodes from the request
        num_nodes = request.form["num_nodes"]
        logger.debug("Number of nodes requested: " + str(num_nodes))

        # Verify the input is all there, notify user if missing any or invalid
        error = []
        if script is None or script.filename == "":
            error.append("Missing script file")
        if dockerfile is None or dockerfile.filename == "":
            error.append("Missing dockerfile")
        if datadesc is None or datadesc.filename == "":
            error.append("Missing data description file")
        if num_nodes is None:
            error.append("Missing number of input nodes")
        else:
            try:
                num_nodes = int(num_nodes)
                if num_nodes < 1:
                    error.append("Number of nodes must be at least 1")
                elif num_nodes > int(os.environ["MAX_NODES"]):
                    error.append("Number of nodes must be no more than " + str(os.environ["MAX_NODES"]))
            except ValueError:
                error.append("Number of nodes must be an integer")

        if error:
            for msg in error:
                flash(msg)
            return redirect(request.url)

        # Generate unique job ID and make a directory for it
        job_id = str(uuid4())
        job_path = os.path.join(os.environ["JOBS_FOLDER"], job_id)
        if not os.path.exists(job_path):
            os.makedirs(job_path)

        # Save the uploaded files
        save_file(job_path, script)
        save_file(job_path, dockerfile)
        save_file(job_path, datadesc)

        # Start job with uploaded files
        logger.debug("job manager url: %s", get_job_manager_url())
        try:
            requests.post(get_job_manager_url(), json = {"id": job_id, "num_nodes": num_nodes})
        except Exception as e:
            logger.debug("Failed to post to manager: %s", e)

        return redirect(url_for("job_submitted",
                                job_id=job_id,
                                script=script.filename,
                                dockerfile=dockerfile.filename,
                                datadesc=datadesc.filename,
                                num_nodes=num_nodes))

    return render_template("submit.html", max_nodes = os.environ["MAX_NODES"])

# Show a submission confirmation screen
@app.route("/submitted/")
def job_submitted():
    job_id = request.args["job_id"]
    script = request.args["script"]
    dockerfile = request.args["dockerfile"]
    datadesc = request.args["datadesc"]
    num_nodes = request.args["num_nodes"]
    return render_template("submitted.html",
                           job_id=job_id,
                           script_file=script,
                           dockerfile=dockerfile,
                           data_file=datadesc,
                           num_nodes=num_nodes)

# Redirect home to submit job page
@app.route("/")
def hello_world():
    logger.debug("Hello World! This is a debug message.")
    return redirect(url_for("submit_job"))
