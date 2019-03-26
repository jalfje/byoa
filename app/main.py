import os
import sys
import logging
from flask import Flask, request, flash, redirect, send_from_directory, url_for, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
# This somehow doesn"t work with relative paths
app.config["UPLOAD_FOLDER"] = "/home/jamie/Documents/School/byoa/uploads/"
# 32 MB max upload size
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# Set up logging
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
#logger = logging.getLogger(__name__)
#logger.addHandler(handler)
logger = app.logger
#logger.addHandler(handler)

@app.route("/")
def hello_world():
    logger.debug("Hello World! This is a debug message.")
    return "Hello World!"

# Save a file
def upload_file(the_file):
    filename = secure_filename(the_file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    the_file.save(path)
    logger.debug("Saved file to %s", path)

@app.route("/submit/", methods=["GET", "POST"])
def submit_files():
    if request.method == "POST":
        # class of request.files is werkzeug.ImmutableMultiDict
        logger.debug("Job submitted with request files: " + str(request.files))
        # Get our 3 files from the request
        script = request.files.get("script")
        dockerfile = request.files.get("dockerfile")
        datadesc = request.files.get("datadesc")
        logger.debug("Script file: " + str(script))
        logger.debug("Dockerfile: " + str(dockerfile))
        logger.debug("Data desc file: " + str(datadesc))
        # Verify the files all exist
        # TODO: fix "flash" not working ("secret key not set"?)
        if script is None or script.filename == "":
            flash("Missing script file")
            return redirect(request.url)
        if dockerfile is None or dockerfile.filename == "":
            flash("Missing dockerfile")
            return redirect(request.url)
        if datadesc is None or datadesc.filename == "":
            flash("Missing data description file")
            return redirect(request.url)
        # Save the uploaded files
        upload_file(script)
        upload_file(dockerfile)
        upload_file(datadesc)
        return redirect(url_for("job_submitted", script=script.filename, dockerfile=dockerfile.filename, datadesc=datadesc.filename))

    return render_template("submit.html")

@app.route("/submitted/")
def job_submitted():
    script = request.args["script"]
    dockerfile = request.args["dockerfile"]
    datadesc = request.args["datadesc"]
    return render_template("submitted.html", script_file=script, dockerfile=dockerfile, data_file=datadesc)
