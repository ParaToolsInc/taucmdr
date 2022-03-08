FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive set -v && \
        apt-get update && \
        apt-get install -y --no-install-recommends ca-certificates curl default-jre wget openssh-server libz-dev m4 make locales git gcc g++ gfortran mpi-default-bin mpi-default-dev python-dev python3-dev && \
        rm -rf /var/lib/apt/lists/* && \
        localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
        useradd -ms /bin/bash tau
ENV LANG=en_US.UTF-8 INSTALLDIR=/home/tau/taucmdr __TAUCMDR_DEVELOPER__=1
COPY .gitignore .gitattributes .version.sh LICENSE README.md Makefile setup.py MANIFEST.in requirements-dev.txt /tmp/taucmdr/
COPY scripts /tmp/taucmdr/scripts
COPY packages /tmp/taucmdr/packages
COPY docs /tmp/taucmdr/docs
COPY examples /tmp/taucmdr/examples
COPY .testfiles /tmp/taucmdr/.testfiles
COPY .git /tmp/taucmdr/.testfiles
WORKDIR /tmp/taucmdr
RUN ls -la ; make clean ; mkdir ${INSTALLDIR}; make install; chown -R tau:tau ${INSTALLDIR}
USER tau
WORKDIR /home/tau/src
ENV PATH="/home/tau/taucmdr/conda/bin:$PATH:/home/tau/taucmdr/bin"
ENV __TAUCMDR_SYSTEM_PREFIX__="/home/tau/taucmdr/system"
ENV __TAUCMDR_USER_PREFIX__="/dev/shm/taucmdr_user"
