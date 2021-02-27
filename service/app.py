import imghdr
from flask_dropzone import Dropzone
import os
from flask import Flask, render_template, request, redirect, url_for, abort, \
    send_from_directory, current_app, jsonify
from werkzeug.utils import secure_filename
from processing import process_file

dropzone = Dropzone()
app = Flask(__name__)
dropzone.init_app(app)
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.nii', '.zip']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['DROPZONE_MAX_FILES'] = 1
app.config['DROPZONE_MAX_FILE_SIZE'] = 1000
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = '.zip, .nii, .nii.gz'
app.config['DROPZONE_REDIRECT_VIEW'] = 'viewer'

db = {}


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)


@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files.get('file')
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return "Invalid image", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        db['file'] = os.path.join(app.config['UPLOAD_PATH'], filename)
    return "", 200


@app.route('/viewer')
def viewer():
    return render_template('viewer.html')


@app.route('/process')
def process():
    file = db.get('file')
    if file is None:
        return jsonify({"status": "err"}, 404)
    result = process_file(file_path=file)
    if result:
        return jsonify({"status": "ok", "result": result}, 200)
    return {"status": "err"}, 500


@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    downloads = os.path.join(current_app.root_path, app.config['DOWNLOAD_FOLDER'])
    return send_from_directory(directory=downloads, filename=filename)


if __name__ == '__main__':

    app.run(host="0.0.0.0")