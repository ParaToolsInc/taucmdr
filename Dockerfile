ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION}

# The tau user's UID in the image
ARG TAU_UID=1000
# The Python version used for the uv environment into which we install taucmdr 
ARG PYTHON_VERSION=3.15

RUN set -e && export DEBIAN_FRONTEND=noninteractive && \
        apt-get update && \
        apt-get install -y --no-install-recommends ca-certificates locales default-jre \
            gcc g++ gfortran make m4 cmake perl bzip2 xz-utils zlib1g-dev git curl \
            openmpi-bin openmpi-common libopenmpi-dev python3-dev python-is-python3 && \
        rm -rf /var/lib/apt/lists/* && \
        localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
        if id ubuntu > /dev/null 2>&1; then userdel -r ubuntu; fi && \
        useradd -m -s /bin/bash -u ${TAU_UID} tau
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/
ENV LANG=en_US.UTF-8

# setuptools-scm needs the checkout's .git to set the version.
COPY --chown=tau:tau . /tmp/taucmdr
USER tau
# The development requirements let scripts/run_tests.py run with the tool's Python.
RUN uv tool install --python ${PYTHON_VERSION} --with-requirements /tmp/taucmdr/requirements-dev.txt /tmp/taucmdr
# Mount a volume for the system storage level
RUN mkdir /home/tau/system
ENV PATH="/home/tau/.local/bin:${PATH}"
ENV __TAUCMDR_USER_PREFIX__="/dev/shm/taucmdr_user"
WORKDIR /home/tau/src
