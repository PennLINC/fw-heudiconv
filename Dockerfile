#flywheel/fmriprep

FROM python:3.7-alpine
MAINTAINER Matt Cieslak <matthew.cieslak@pennmedicine.upenn.edu>

# Install basic dependencies
RUN apk add --no-cache tar zip

# Install the Flywheel SDK
RUN pip install flywheel-sdk~=5.0.4

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/fwheudiconv_run.py"]

# Copy over python scripts that generate the BIDS hierarchy
COPY . /src
RUN cd /src \
    && pip install .

COPY fw_heudiconv_run.py /flywheel/v0/fw_heudiconv_run.py
RUN chmod +x ${FLYWHEEL}/*

# ENV preservation for Flywheel Engine
RUN env -u HOSTNAME -u PWD | \
  awk -F = '{ print "export " $1 "=\"" $2 "\"" }' > ${FLYWHEEL}/docker-env.sh

WORKDIR /flywheel/v0
