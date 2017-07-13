# Dockerfile to build a Fedora system with installed web server
# and Adverb to run as a service on your localhost.
#

# Clone from the Fedora 25 image
FROM fedora:25

# Chuck Rolke
LABEL maintainer "crolke@redhat.com"

USER root

# Clone from the Fedora 25 image
FROM fedora:25

# Install required packages
RUN dnf install -y \
    git            \
    httpd          \
    python         \
    wireshark

# Clone and install Adverb
WORKDIR /adverb
RUN git clone https://github.com/ChugR/Adverb

WORKDIR /adverb/Adverb
RUN /bin/bash ./copy-util.sh installindex

# Add root to the wireshark group
RUN usermod -a -G wireshark root

# Give httpd a server name
RUN echo 'ServerName localhost' >> /etc/httpd/conf/httpd.conf

# Expose the httpd service port
EXPOSE 80

# Start up httpd.
ENTRYPOINT /usr/sbin/httpd -DFOREGROUND
