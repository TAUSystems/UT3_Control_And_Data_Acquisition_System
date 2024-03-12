# syntax=docker/dockerfile:1

# NOTE: This Dockerfile is meant to be run from the root of this repository, i.e.
# from this data_uplader directory, navigate up three parents: cd ../../..

# See epics/client/data_uploader/README.md for instructions. The build command is
#   docker build \
#     -f epics/client/data_uploader/Dockerfile \
#     -t data-uploader \
#     --build-arg IMAGE_BACKEND_ENDPOINT_URL=http://12.34.56.78:1234/daq-image \
#     .
#

ARG PYTHON_VERSION=3.11.7
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Add environment variables
ARG IMAGE_BACKEND_ENDPOINT_URL
ENV IMAGE_BACKEND_ENDPOINT_URL=${IMAGE_BACKEND_ENDPOINT_URL}

# Copy the source code into the container.
COPY ./epics/client/data_uploader ./epics/client/data_uploader
COPY ./measurement_db ./measurement_db

# install MariaDB Connector
RUN apt update && \
    apt install -y wget curl gcc
RUN cd /tmp && \
    wget https://r.mariadb.com/downloads/mariadb_repo_setup && \
    echo "30d2a05509d1c129dd7dd8430507e6a7729a4854ea10c9dcf6be88964f3fdc25  mariadb_repo_setup" \
        | sha256sum -c -  && \
    chmod +x mariadb_repo_setup  && \
    ./mariadb_repo_setup --mariadb-server-version="mariadb-10.11" && \
    apt install -y libmariadb3 libmariadb-dev 

# install project and dependencies
RUN python -m pip install ./epics/client/data_uploader
RUN ln -s ./epics/client/data_uploader/run.py run.py

# Switch to the non-privileged user to run the application.
USER appuser

# Run the application.
CMD python run.py
