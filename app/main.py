import os
import sys
import logging
from flask import Flask, request, flash, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/home/jamie/Documents/School/byoa/uploads/"
# 32 MB max upload size
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
# restricted upload file extensions
ALLOWED_EXTENSIONS = set(["py", "dockerfile", "json"])

# Set up logging
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
#logger = logging.getLogger(__name__)
#logger.addHandler(handler)
logger = app.logger
logger.addHandler(handler)

@app.route("/")
def hello_world():
    logger.debug("Hello World! This is a debug message.")
    return "Hello World!"

def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and ext in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    directory = app.config['UPLOAD_FOLDER']
    logger.debug("Returning file from %s", os.path.join(directory, filename))
    return send_from_directory(directory, filename)
    return send_from_directory("/home/jamie/Documents/School/byoa/uploads/", filename)

@app.route("/upload/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        logger.debug(request.files)
        if "file" not in request.files:
            flash("No file uploaded")
            return redirect(request.url)
        upload = request.files["file"]
        logger.debug(upload)
        if upload.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if upload and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.debug("Saving to %s", upload_path)
            upload.save(upload_path)
            return redirect(url_for('uploaded_file', filename=filename))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''
