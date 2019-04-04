import os
import sys
import logging
import requests
from uuid import uuid4
from flask import Flask, request, flash, redirect, send_from_directory, url_for, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super duper secret key! idk why this needs to be here but it does"
# This somehow doesn"t work with relative paths
app.config["UPLOAD_FOLDER"] = "/home/jamie/Documents/School/byoa/uploads/"
# 32 MB max upload size
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# Set up logging
#formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
#handler = logging.StreamHandler(sys.stdout)
#handler.setLevel(logging.DEBUG)
#handler.setFormatter(formatter)
#logger = logging.getLogger(__name__)
#logger.addHandler(handler)
logger = app.logger

@app.route("/")
def hello_world():
    logger.debug("Hello World! This is a debug message.")
    return redirect(url_for("submit_files"))

# Save a file
def save_file(directory, file_obj):
    filename = secure_filename(file_obj.filename)
    path = os.path.join(directory, filename)
    file_obj.save(path)
    logger.debug("Saved file to %s", path)

@app.route("/submit/", methods=["GET", "POST"])
def submit_files():
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
        job_path = os.path.join(app.config["UPLOAD_FOLDER"], job_id)
        if not os.path.exists(job_path):
            os.makedirs(job_path)

        # Save the uploaded files
        save_file(job_path, script)
        save_file(job_path, dockerfile)
        save_file(job_path, datadesc)

        # Start job with uploaded files
        job_manager_url = "http://job_manager_host_name:job_manager_port/"
        requests.post(job_manager_url, data = {"id": job_id, "path": job_path})

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
