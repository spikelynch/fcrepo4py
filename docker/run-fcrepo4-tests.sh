#!/usr/bin/env bash

# Runs the test suite for fcrepo4.py

DELAY=2000

echo "Sleeping for $DELAY secs..."
sleep $DELAY
cd /opt/fcrepo4py
cp /code/config.yml ./
python setup.py test
