import os
import sys
import logging
from flask import Flask, request, flash, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
# This somehow doesn't work with relative paths
app.config['UPLOAD_FOLDER'] = "/home/jamie/Documents/School/byoa/uploads/"
app.config['HTML_FOLDER'] = "/home/jamie/Documents/School/byoa/html/"
# 32 MB max upload size
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

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
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    the_file.save(path)
    logger.debug("Saved file to %s", path)

@app.route("/submit/", methods=["GET", "POST"])
def submit_files():
    if request.method == "POST":
        # class of request.files is werkzeug.ImmutableMultiDict
        logger.debug("Request files: " + str(request.files))
        # Get our 3 files from the request
        script = request.files.get("script")
        dockerfile = request.files.get("dockerfile")
        datadesc = request.files.get("datadesc")
        # Verify the files all exist
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
        return redirect(url_for('uploaded_file', filename=filename))

    return send_from_directory(app.config['HTML_FOLDER'], "submit.html")
