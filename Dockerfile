FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Install system dependencies and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

WORKDIR /workspace

# Expose application port
EXPOSE 2029

# Set default command (can be changed as needed)
CMD ["/bin/bash"]
# To run the container with unlimited memory, port mapping, workspace mount, and a specific name:
# docker build -t askrgipt .
# docker run --gpus all --name Ask-RGIPT -p 2029:2029 -v /mnt/c/git/AskRGIPT:/workspace askrgipt:latest
