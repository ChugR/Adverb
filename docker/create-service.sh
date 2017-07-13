#!/bin/bash
#
# Creates a service to run amqp-adverb in a docker container.
#   systemctl service start amqp-adverb
#
# Then browse to http://<dockerhost>:8080/
#          or to http://<dockerhost>:8080/adverb.html
#
cat > /etc/systemd/system/amqp-adverb.service <<EOF
[Unit]
Description=AMQP Adverb Dockerized Container
After=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/docker run -p 8080:80 local:amqp-adverb
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
