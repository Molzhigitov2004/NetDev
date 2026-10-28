# Docker file - instructions to build an image
# Getting base image
FROM ubuntu:26.04

# disables interactive prompt during installations
ENV DEBIAN_FRONTEND=noninteractive

# RUN used to run any commands inside the container on startup
RUN apt update && apt install -y python3-pip ansible vim openssh-client
RUN pip install --break-system-packages ansible-pylibssh==1.4.0

# specify a working directory
# WORKDIR basically creates given dir and moves each following RUN into it
WORKDIR /app
# COPY used to copy from host os ro the container, here we copy all . and copy it to the workdir
COPY . /app

# fix for freaking ssh keys
COPY ssh_config /root/.ssh/config
