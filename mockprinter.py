import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route("/")
def index():
    return "hi"


ALLOWED_EXTENSIONS = {"gcode"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/print_file_uploads", methods=["POST"])
def file():
    if "print_file" not in request.files:
        print("err file not found in post")
        return "err"
    file = request.files["print_file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join("./tmp", filename))
        return "ok saved"


@app.route("/command", methods=["POST"])
def command():
    print(request.form)
    return "ok"


app.run()