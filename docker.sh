#!/bin/bash
mkdir /tmp/uploads
mkdir /tmp/downloads
docker build -t covid19-seg . && docker run -td -v /tmp/uploads:/app/uploads -v /tmp/downloads:/app/downloads -p 8090:5000 covid19-seg