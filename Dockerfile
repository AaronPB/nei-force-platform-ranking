FROM ubuntu:22.04
LABEL maintainer="AaronPB"

# Install base dependencies and Python 3.10 (default on ubuntu 22.04)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    software-properties-common \
    python3 \
    python3-pip

# Install Phidget dependency and clean up cache
RUN curl -fsSL https://www.phidgets.com/downloads/setup_linux | bash &&\
    apt-get install -y libphidget22 libusb-1.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Clone the nei-foce-platform-ranking repository
RUN git clone --depth 1 https://github.com/AaronPB/nei-force-platform-ranking.git /app

# Define workdir as the cloned repository
WORKDIR /app

# Install python dependencies from the cloned repository's requirements.txt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_store/health

# Define entrypoint for Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
