import os
import logging
import requests
from uuid import uuid4
from flask import Flask, request, flash, redirect, send_from_directory, url_for, render_template
from werkzeug.utils import secure_filename


app = Flask(__name__)

# This is for some reason necessary for message flashing
app.secret_key = "super duper secret key!"

# 32 MB max upload size
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# Set up logging
logger = app.logger


# Save a file
def save_file(directory, file_obj):
    filename = secure_filename(file_obj.filename)
    path = os.path.join(directory, filename)
    file_obj.save(path)
    logger.debug("Saved file to %s", path)

# Get the job manager's URL
def get_job_manager_url():
    host = os.environ["MANAGER_HOST"]
    port = os.environ["MANAGER_PORT"]
    url = "http://" + host + ":" + port + "/"
    return url

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
        logger.debug("Data desc file: " + str(datadesc))

        # Verify the files all exist, notify user if missing any
        error = []
        if script is None or script.filename == "":
            error.append("Missing script file")
        if dockerfile is None or dockerfile.filename == "":
            error.append("Missing dockerfile")
        if datadesc is None or datadesc.filename == "":
            error.append("Missing data description file")
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
            requests.post(get_job_manager_url(), json = {"id": job_id, "path": job_path})
        except Exception as e:
            logger.debug("Failed to post to manager: %s", e)

        # TODO: put job ID into return html somewhere
        return redirect(url_for("job_submitted", script=script.filename, dockerfile=dockerfile.filename, datadesc=datadesc.filename))

    return render_template("submit.html")

# Show a submission confirmation screen
@app.route("/submitted/")
def job_submitted():
    script = request.args["script"]
    dockerfile = request.args["dockerfile"]
    datadesc = request.args["datadesc"]
    return render_template("submitted.html", script_file=script, dockerfile=dockerfile, data_file=datadesc)

# Redirect home to submit job page
@app.route("/")
def hello_world():
    logger.debug("Hello World! This is a debug message.")
    return redirect(url_for("submit_job"))
