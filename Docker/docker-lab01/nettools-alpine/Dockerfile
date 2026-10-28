FROM alpine:3.22
LABEL org.opencontainers.image.title=nettools
WORKDIR /app
RUN apk add --no-cache iproute2 iputils mtr bind-tools netcat-openbsd tcpdump curl net-snmp-tools bash
CMD ["bash"]

