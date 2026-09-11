#!/bin/bash
set -e
source /opt/venv/bin/activate
F=/home/submit/lavezzo/alphaS/WRemnants/wremnants/postprocessing/scetlib_ad/np_damping_wall.py
python3 -m black --version; python3 -m isort --version
python3 -m isort "$F"
python3 -m black "$F"
python3 -m flake8 --max-line-length 100 --extend-ignore E203,W503,E501 "$F" && echo FLAKE8_OK
