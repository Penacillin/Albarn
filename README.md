# Albarn

## Installation
```bash
pip install -r requirements.txt
```

## Setup
Run:
```bash
inv setup
```
or manually put the `acsmdownloadeder` binary into `bin/`

Create a `config.json`, follow `example-config.json`. The defaults section is optional, specifying
device/activation files will make the `/convert_acsm` endpoint's device fields optional.

## Run
```bash
uvicorn main:app
```

## Usage
Visit `http://url/docs` to see docs on the endpoints
