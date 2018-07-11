# Dockerfile to build a Fedora system with installed web server
# with Adverb to run on your localhost.
#

# Clone from a Fedora image
FROM fedora:27

# Chuck Rolke
LABEL maintainer "crolke at redhatdotcom"

USER root

# Install required packages
RUN dnf install -y \
    git            \
    httpd          \
    python         \
    wireshark

# add root to the wireshark group;
# give httpd a server name
RUN /bin/bash -c \
    "usermod -a -G wireshark root; \
    echo 'ServerName localhost' >> /etc/httpd/conf/httpd.conf"

# Expose the httpd service port
EXPOSE 80

# Start up httpd.
ENTRYPOINT /usr/sbin/httpd -DFOREGROUND

# Typical builds specify a CACHEBUST arg > 1
# so that cacheing is disabled from here on out.
# This gets the latest upstream Adverb clone
# and installs it.
ARG CACHEBUST=1

# clone Adverb;
# install Adverb;
RUN /bin/bash -c \
    "mkdir /adverb; \
    cd /adverb; \
    git clone https://github.com/ChugR/Adverb; \
    cd Adverb; \
    ./copy-util.sh installindex"
