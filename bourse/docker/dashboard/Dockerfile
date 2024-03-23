FROM python:3-bookworm
#FROM ubuntu:latest
MAINTAINER Olivier Ricou <olivier@ricou.eu.org>

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update                              \
    && apt-get install -y --no-install-recommends   \
        python3 \
        git \
        make \
        python3-pip \
        python3-setuptools \
        tzdata \
        postgresql-client \
        ffmpeg                                                  \
        libx264-dev                                             \
        libzmq3-dev                                             \
        libxml2-dev                                             \
        libxslt-dev                                             \
        zlib1g-dev                                              \
        liblapack-dev                                           \
        gfortran

RUN pip3 install pip --upgrade
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG en_US.
ENV PYTHONPATH "${PYTHONPATH}:/home/ricou/.local/lib/python3/site-packages/"

RUN cp /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

RUN adduser --disabled-password --gecos "" bourse
RUN chmod 755 /home/bourse
USER bourse
WORKDIR /home/bourse

ENV PATH "${PATH}:/home/bourse/.local/bin/"
# Copy the rest of the codebase into the image

ADD apps.tgz .

# Finally, run gunicorn.
#CMD echo $PYTHONPATH; python3 bourse.py
CMD [ "gunicorn", "--timeout=300", "--workers=5", "--threads=1", "-b 0.0.0.0:8050", "bourse:server"]

