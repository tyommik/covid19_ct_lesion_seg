#!/bin/bash
docker build -t covid19-seg . && docker run -p 8090:5000 covid19-seg