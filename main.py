import base64
import os
import sys
import logging
import pathlib
import tempfile
import json
from flask import Flask, request
from google.cloud import storage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import mlink_img_optimizer


CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET', None)
if CLOUD_STORAGE_BUCKET is None:
    logger.error("Missing 'CLOUD_STORAGE_BUCKET' environment variable!")


CLOUD_UPLOAD_STORAGE_BUCKET = os.environ.get('CLOUD_UPLOAD_STORAGE_BUCKET', None)
if CLOUD_UPLOAD_STORAGE_BUCKET is None:
    logger.error("Missing 'CLOUD_UPLOAD_STORAGE_BUCKET' environment variable!")


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    print(f"Envelope -> {envelope}")
    pubsub_message = envelope['message']

    name = 'World'
    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        name = base64.b64decode(pubsub_message['data']).decode('utf-8').strip()

        payload = json.loads(name)
        if 'bucket' in payload:
            # Storage Bucket notification message

            print("Working on image..")
            print(f'Got pub/sub notification message: {payload}')
            filename = pathlib.Path(payload.get('name'))
            gcs = storage.Client()
            bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
            bucket_upload = gcs.get_bucket(CLOUD_UPLOAD_STORAGE_BUCKET)
            blob = bucket.get_blob(filename.name)
            # blob = bucket.blob(filename.name)
            if blob is None:
                print(f"Unable to find file: {filename} from {CLOUD_STORAGE_BUCKET}")
                sys.stdout.flush()
                return (f"Unable to find file: {filename} from {CLOUD_STORAGE_BUCKET}", 204)
            else:
                with tempfile.NamedTemporaryFile(suffix=filename.suffix) as file_obj:
                    print(f"Downloading from GCS bucket {bucket} / {blob} to local temp file: {file_obj}")
                    blob.download_to_file(file_obj)
                    file_obj.seek(0)  # rewind to beginning of file

                    print("Running optimization...")
                    old_size = blob.size
                    report = mlink_img_optimizer.optimize(file_obj.name)
                    file_obj.seek(0)  # rewind to beginning of file
                    new_size = os.fstat(file_obj.file.fileno()).st_size

                    # Debugging in GCP logs
                    print(report)

                    if report.get('percent') > 10.0:
                        print(f"Image was optimized - upload new image to bucket!")
                        upload_blob = bucket_upload.blob(filename.name)
                        upload_blob.upload_from_filename(file_obj.name)
                        print(f"Updated image upload to bucket! {file_obj.name} -> {bucket_upload}")
                    else:
                        print(f"Optimization percent zero - so don't update bucket image. {file_obj.name}")

                    sys.stdout.flush()
                    return (report, 204)

    print(f'Hello {name}!')

    sys.stdout.flush()
    return ('', 204)

@app.route('/status', methods=['GET'])
def status():
    return ('It works', 200)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)
