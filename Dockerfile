#flywheel/fmriprep

FROM python:3
MAINTAINER Matt Cieslak <matthew.cieslak@pennmedicine.upenn.edu>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/fw_heudiconv_run.py"]

# Copy over python scripts that generate the BIDS hierarchy
RUN apt-get -y update
RUN apt-get install -y zip
RUN pip install --no-cache heudiconv flywheel-sdk pandas
COPY . /src
RUN cd /src \
    && pip install . \
    && pip install --no-cache --no-deps heudiconv \
    && pip install --no-cache flywheel-sdk \
    && pip install --no-cache nipype \
    && rm -rf /src \
    && apt-get install -y --no-install-recommends zip

COPY fw_heudiconv_run.py /flywheel/v0/fw_heudiconv_run.py
RUN chmod +x ${FLYWHEEL}/*

# ENV preservation for Flywheel Engine
RUN env -u HOSTNAME -u PWD | \
  awk -F = '{ print "export " $1 "=\"" $2 "\"" }' > ${FLYWHEEL}/docker-env.sh

WORKDIR /flywheel/v0
