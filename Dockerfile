FROM ubuntu:22.04
LABEL maintainer="AaronPB"

# Install base dependencies and Python 3.10 (default on ubuntu 22.04)
RUN apt-get update && apt-get install -y \
    curl \
    software-properties-common \
    python3 \
    python3-pip

# TODO Install git and clone this repository into docker container, instead of copy.

# Install dependencies
## Phidget
RUN curl -fsSL https://www.phidgets.com/downloads/setup_linux | bash &&\
    apt-get install -y libphidget22

# Install python and python dependencies
COPY requirements.txt requirements.txt

# Use python3 -m pip to install dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Define workdir and copy project
ENV prj_dir=/app/
WORKDIR ${prj_dir}
COPY . ${prj_dir}

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_store/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
