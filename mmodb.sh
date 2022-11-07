#!/bin/bash
set -e
# NOTE: presently this mongo database is open to anyone on localhost.
#       THIS IS BAD
mkdir -p mmodb
mongod --port 27000 --dbpath mmodb
