# Dockerfile
FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime
 
# Remove any third-party apt sources to avoid issues with expiring keys.
RUN rm -f /etc/apt/sources.list.d/*.list
 
# Install some basic utilities & python prerequisites
RUN apt-get update -y && apt-get install -y --no-install-recommends\
    wget \
    vim \
    curl \
    ssh \
    tree \
    sudo \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# Set up time zone
ENV TZ=Asia/Seoul
RUN sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# pip
RUN python -m pip install --upgrade pip

WORKDIR /app
COPY . .
