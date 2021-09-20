from invoke import task
import urllib.request
import os


@task
def setup(
        c,
        acsmdownloader_url="https://github.com/Penacillin/knocker/releases/download/v0.1.0/acsmdownloader-v0.1.0-linux-amd64"):
    urllib.request.urlretrieve(acsmdownloader_url, "bin/acsmdownloader")
    os.chmod('bin/acsmdownloader', 0o750)
