#!/bin/bash
set -e
mkdir -p mmodb
mongod --port 27000 --dbpath mmodb
