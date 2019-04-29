#flywheel/fmriprep

FROM alpine:latest
MAINTAINER Matt Cieslak <matthew.cieslak@pennmedicine.upenn.edu>

RUN apk --no-cache --update-cache add py3-numpy bash zip
RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/fw_heudiconv_run.py"]

# Copy over python scripts that generate the BIDS hierarchy
COPY . /src
RUN cd /src \
    && pip install . \
    && pip install --no-cache --no-deps heudiconv \
    && pip install --no-cache flywheel-sdk \
    && rm -rf /src

COPY fw_heudiconv_run.py /flywheel/v0/fw_heudiconv_run.py
RUN chmod +x ${FLYWHEEL}/*

# ENV preservation for Flywheel Engine
RUN env -u HOSTNAME -u PWD | \
  awk -F = '{ print "export " $1 "=\"" $2 "\"" }' > ${FLYWHEEL}/docker-env.sh

WORKDIR /flywheel/v0
