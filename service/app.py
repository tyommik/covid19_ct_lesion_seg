import imghdr
from flask_dropzone import Dropzone
import os
from flask import Flask, render_template, request, \
    send_from_directory, current_app, jsonify, make_response
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
app.config['DROPZONE_TIMEOUT'] = 120000

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
    file = request.files['file']

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_PATH'], filename)
    current_chunk = int(request.form['dzchunkindex'])
    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))
    try:
        with open(save_path, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong
        # log.exception('Could not write to file')
        return make_response(("Not sure why,"
                              " but we couldn't write the file to disk", 500))
    total_chunks = int(request.form['dztotalchunkcount'])
    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
            # log.error(f"File {file.filename} was completed, "
            #           f"but has a size mismatch."
            #           f"Was {os.path.getsize(save_path)} but we"
            #           f" expected {request.form['dztotalfilesize']} ")
            return make_response(('Size mismatch', 500))
        else:
            pass
            # log.info(f'File {file.filename} has been uploaded successfully')
    else:
        pass
        # log.debug(f'Chunk {current_chunk + 1} of {total_chunks} '
        #           f'for file {file.filename} complete')
    db['file'] = os.path.join(app.config['UPLOAD_PATH'], filename)
    return make_response(("Chunk upload successful", 200))


@app.route('/viewer')
def viewer():
    return render_template('viewer.html')


@app.route('/demo')
def demo():
    return render_template('demo.html')


@app.route('/process')
def process():
    file = db.get('file')
    if file is None:
        return jsonify({"status": "err"}, 404)
    result = process_file(file_path=file)
    del db['file']
    if result:
        return jsonify({"status": "ok", "result": result}, 200)
    return {"status": "err"}, 500


@app.route('/downloads/<path:filename>', methods=['GET'])
def download(filename):
    downloads = os.path.join(current_app.root_path, app.config['DOWNLOAD_FOLDER'])
    return send_from_directory(directory=downloads, filename=filename)


if __name__ == '__main__':
    app.run(host="0.0.0.0")