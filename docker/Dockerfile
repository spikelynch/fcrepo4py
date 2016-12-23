#########################
#
# Dockerfile to run CI tests for fcrepo4py
#
# Mike Lynch 2016 Michael.Lynch@uts.edu.au
#
#########################

FROM python:3
MAINTAINER Michael.Lynch@uts.edu.au

RUN apt-get install -y apt-utils

RUN apt-get update 
RUN apt-get install -y make
RUN apt-get install -y git-core

RUN git clone https://codeine.research.uts.edu.au/eresearch/fcrepo4py.git /opt/fcrepo4py

RUN cd /opt/fcrepo4py && python setup.py install



