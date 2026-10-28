FROM ubuntu:24.04
LABEL org.opencontainers.image.title=nettools

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt-get install -y --no-install-recommends \
    iproute2 iputils-ping traceroute mtr-tiny dnsutils netcat-openbsd tcpdump curl snmp \
    && rm -rf /var/lib/apt/lists/* 

WORKDIR /app

ENTRYPOINT ["ping", "-c", "3"]
CMD ["192.168.197.2"]
