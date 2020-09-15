FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive set -v && \
        apt-get update && \
        apt-get install -y --no-install-recommends curl wget make locales git gcc g++ gfortran mpi-default-bin mpi-default-dev && \
        rm -rf /var/lib/apt/lists/* && \
        localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
        useradd -ms /bin/bash tau
ENV LANG en_US.utf8
USER tau
WORKDIR /home/tau
ENV INSTALLDIR=/home/tau/taucmdr
