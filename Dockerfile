# set base image (host OS)
FROM nvidia/cuda:11.2.1-base

# Set working directory
WORKDIR /app

# Install pip and git
RUN apt update
RUN apt install python3-pip -y
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
RUN apt install git-all -y

# Copy the dependencies file to working directory
COPY requirements.txt .

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy content of local /src directory to working directory
COPY service/ .

RUN mkdir uploads && mkdir downloads

# Start application
CMD [ "python3", "./app.py" ]