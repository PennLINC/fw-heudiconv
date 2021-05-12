#flywheel/fmriprep

FROM python:3.7
MAINTAINER Tinashe Tapera <taperat@pennmedicine.upenn.edu>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/fw_heudiconv_run.py"]

# Copy over python scripts that generate the BIDS hierarchy
RUN apt-get -y update && apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash
RUN apt-get -y update && apt-get install -y zip nodejs
RUN npm install -g bids-validator
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache nipype pathvalidate
RUN pip install --no-cache flywheel-sdk~=14.6.5

COPY . /src

RUN cd /src \
    && pip install . \
    && rm -rf /src

COPY fw_heudiconv_run.py /flywheel/v0/fw_heudiconv_run.py
RUN chmod +x ${FLYWHEEL}/*

# ENV preservation for Flywheel Engine
RUN env -u HOSTNAME -u PWD | \
  awk -F = '{ print "export " $1 "=\"" $2 "\"" }' > ${FLYWHEEL}/docker-env.sh

WORKDIR /flywheel/v0
