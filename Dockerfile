FROM ubuntu:22.04
LABEL maintainer="AaronPB <aaron.pb@psa.es>"
LABEL version="1.0.0"
LABEL description="Una aplicación interactiva con plataformas de fuerza para la Noche Europea de los Investigadores."
LABEL license="GPL-3.0-or-later"
LABEL repository="https://github.com/AaronPB/nei-force-platform-ranking"
LABEL org.opencontainers.image.source="https://github.com/AaronPB/nei-force-platform-ranking"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.title="NEI Force Platform Ranking"
LABEL org.opencontainers.image.description="Una aplicación interactiva con plataformas de fuerza para la Noche Europea de los Investigadores."


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

# Define the workdir path and copy the repository content
WORKDIR /app
COPY . /app

# Install python dependencies from the cloned repository's requirements.txt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_store/health

# Define entrypoint for Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
