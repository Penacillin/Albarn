import os
import tempfile
import re
from urllib.parse import urljoin, quote
import json
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import subprocess

os.makedirs('.temp', exist_ok=True)
os.makedirs('output', exist_ok=True)
app = FastAPI()
logger = logging.getLogger('gunicorn.error')

CREATED_RE = re.compile('.*Created (.*)$')

with open('config.json', 'r') as fp:
    config = json.load(fp)
ROOT_URL = config['root_url']
DEFAULT_FILES = {}
if 'defaults' in config:
    for default_file in ['device_file', 'activation_file', 'device_salt']:
        device_filename = config['defaults'].get(default_file, None)
        if device_filename:
            with open(device_filename, 'rb') as fp:
                DEFAULT_FILES[default_file] = fp.read()

logger.info(f"Defaults: {DEFAULT_FILES}")
DEFAULT_DEVICE = DEFAULT_FILES.get('device_file', None)
DEFAULT_ACTIVATION = DEFAULT_FILES.get('activation_file', None)
DEFAULT_KEY = DEFAULT_FILES.get('device_salt', None)

app.mount("/output", StaticFiles(directory="output"), name="static")


class ConvertACSMResponse(BaseModel):
    book_size: int
    book_name: str
    book_link: str
    stdout: str
    stderr: str
    return_code: int


@app.post("/convert_acsm", response_model=ConvertACSMResponse)
async def convert_acsm(
        book: UploadFile = File(...),
        device_file: bytes = File(DEFAULT_DEVICE),
        activation_file: bytes = File(DEFAULT_ACTIVATION),
        device_salt: bytes = File(b'' if DEFAULT_KEY else None)):

    with tempfile.NamedTemporaryFile(dir='.temp', suffix='.xml', delete=False) as df, \
            tempfile.NamedTemporaryFile(dir='.temp', suffix='.xml', delete=False) as af, \
            tempfile.NamedTemporaryFile(dir='.temp', delete=False) as ds, \
            tempfile.NamedTemporaryFile(dir='.temp', suffix='.acsm', delete=False) as book_fp:
        df.write(device_file)
        af.write(activation_file)
        if DEFAULT_KEY and device_salt == b'':
            ds.write(DEFAULT_KEY)
        else:
            ds.write(device_salt)
        contents = await book.read()
        if isinstance(contents, str):
            contents = contents.encode('utf-8')
        book_fp.write(contents)

    completed = subprocess.run(['./bin/acsmdownloader', '-d', df.name, '-a', af.name, '-k',
                                ds.name, '-f', book_fp.name, '-O', 'output'], capture_output=True)
    os.remove(df.name)
    os.remove(af.name)
    os.remove(ds.name)
    os.remove(book_fp.name)

    book_name = None
    book_link = None
    if not completed.stderr:
        res = CREATED_RE.search(completed.stdout.decode('utf-8'))
        if res:
            book_name = res.group(1).split('/')[1]
            book_link = urljoin(ROOT_URL, 'output/' + quote(book_name))

    return {
        "book_size": len(contents),
        "book_name": book_name,
        "book_link": book_link,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "return_code": completed.returncode
    }


@app.get("/acsm")
async def acsm():
    html_content = """
    <html>
        <head>
            <title>Albarn</title>
        </head>
        <body>
            <form action="./convert_acsm" method="post" enctype="multipart/form-data">
                <label for="myfile">Select an acsm file:</label>
                <input type="file" id="myfile" name="book">
                <br>
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)
