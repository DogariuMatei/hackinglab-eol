FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    libpcap-dev \
    curl \
    zmap \
    wget \
    git \
    iproute2 \
    dumb-init \
    libpcap0.8 \
    libjson-c5 \
    libjudydebian1 \
    libgmp10 \
    && rm -rf /var/lib/apt/lists/*

ENV GO_VERSION=1.23.0
RUN wget -q https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

RUN git clone https://github.com/zmap/zgrab2.git /opt/zgrab2 && \
    cd /opt/zgrab2 && \
    make install
ENV PATH=$PATH:/root/go/bin

WORKDIR /scanner

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

COPY . .

ENTRYPOINT ["dumb-init", "--", "python3", "src/main.py"]
