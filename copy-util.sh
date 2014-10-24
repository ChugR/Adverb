#!/bin/bash

function diffFunc {
    set -x
    diff -s ./scripts/html/adverb.html  /var/www/html/adverb.html
    diff -s ./scripts/cgi-bin/adverb.sh /var/www/cgi-bin/adverb.sh
    diff -s ./scripts/adverb.py         /var/www/cgi-bin/adverb/scripts/adverb.py
}

function putFunc {
    set -x
    cp -i ./scripts/html/adverb.html  /var/www/html/adverb.html
    cp -i ./scripts/cgi-bin/adverb.sh /var/www/cgi-bin/adverb.sh
    cp -i ./scripts/adverb.py         /var/www/cgi-bin/adverb/scripts/adverb.py
}

function getFunc {
    set -x
    cp -i /var/www/html/adverb.html                  ./scripts/html/adverb.html
    cp -i /var/www/cgi-bin/adverb.sh                 ./scripts/cgi-bin/adverb.sh
    cp -i /var/www/cgi-bin/adverb/scripts/adverb.py  ./scripts/adverb.py
}

if [ $# -eq 0 ]; then
    diffFunc
    exit 0
fi

if [ -z "$1" ]; then
    diffFunc
    exit 0
fi

if [ "$1" == "diff" ]; then
    diffFunc
    exit 0
fi

if [ "$1" == "get" ]; then
    getFunc
    exit 0
fi

if [ "$1" == "put" ]; then
    putFunc
    exit 0
fi

echo "unknown arg $1"
exit 1
