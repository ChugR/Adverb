#!/bin/bash

docker build -t local:amqp-adverb --build-arg CACHEBUST=$(date +%s) .

# then to publish:
#
# docker images
#  <find the IMAGE ID of the fresh build>
# docker tag <theId> chugr/amqp-adverb
# export DOCKER_ID_USER="chugr"
# docker login
# docker push chugr/amqp-adverb
