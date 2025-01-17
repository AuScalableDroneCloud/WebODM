FROM ubuntu:21.04
MAINTAINER Piero Toffanin <pt@masseranolabs.com>

ARG TEST_BUILD
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/webodm
ENV PROJ_LIB=/usr/share/proj

# Prepare directory
ADD . /webodm/
WORKDIR /webodm

# Use old-releases for 21.04
RUN printf "deb http://old-releases.ubuntu.com/ubuntu/ hirsute main restricted\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute-updates main restricted\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute universe\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute-updates universe\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute multiverse\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute-updates multiverse\ndeb http://old-releases.ubuntu.com/ubuntu/ hirsute-backports main restricted universe multiverse" > /etc/apt/sources.list

# Install Node.js
RUN apt-get -qq update && apt-get -qq install -y --no-install-recommends wget curl apt-utils unzip && \
    wget --no-check-certificate https://deb.nodesource.com/setup_14.x -O /tmp/node.sh && bash /tmp/node.sh && \
    apt-get -qq update && apt-get -qq install -y nodejs && \
    # Install Python3, GDAL, PDAL, nginx, letsencrypt, psql
    apt-get -qq update && apt-get -qq install -y --no-install-recommends python3 python3-pip python3-setuptools python3-wheel git g++ python3-dev python2.7-dev libpq-dev binutils libproj-dev gdal-bin pdal libgdal-dev python3-gdal nginx grass-core gettext-base cron postgresql-client-13 gettext tzdata && \
    update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1 && update-alternatives --install /usr/bin/python python /usr/bin/python3.9 2 && \
    #Debugging utils
    apt-get -qq install -y psmisc curl vim nmap netcat iputils-ping rsync fail2ban && \
    # Install pip reqs
    pip install -U pip && pip install -r requirements.txt "boto3==1.14.14" && \
    # Setup cron so user can start
    chmod u+s /usr/sbin/cron && \
    touch /var/log/cron.log && \
    # Cleanup
    apt-get remove -y g++ python3-dev libpq-dev && apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN /webodm/nodeodm/setup.sh && /webodm/nodeodm/cleanup.sh && cd /webodm && \
    npm install --quiet -g webpack@4.46.0 && npm install --quiet -g webpack-cli@4.10.0 && npm install --quiet && \
    sed -i 's/p-queue/p-queue\/dist/g' ./node_modules/@uppy/provider-views/lib/ProviderView/ProviderView.js && \
    webpack --mode production && \
     echo "UTC" > /etc/timezone && \
    echo "UTC" > /etc/timezone && \
    useradd -m -d "/home/webodm" -s /bin/bash webodm && \
    chown -R webodm:webodm /webodm && \
    mkdir -p /var/lib/nginx/body /var/lib/nginx/fastcgi /var/lib/nginx/proxy /var/lib/nginx/uwsgi /var/lib/nginx/scgi && \
    chown -R webodm:webodm  /var/lib/nginx

USER webodm

#Add the local python package bin dir to PATH
ENV PATH="${PATH}:/home/webodm/.local/bin"

RUN python manage.py collectstatic --noinput && \
    python manage.py rebuildplugins && \
    python manage.py translate build --safe && \
    rm /webodm/webodm/secret_key.py

VOLUME /webodm/app/media
