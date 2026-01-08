FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

COPY .env /root/.env
COPY install.sh /usr/local/bin/install.sh
COPY ssh_setup.sh /usr/local/bin/ssh_setup.sh
RUN chmod +x /usr/local/bin/install.sh /usr/local/bin/ssh_setup.sh

ENV GOPATH=/root/go
ENV PATH=/usr/local/go/bin:/root/go/bin:$PATH

RUN mkdir -p /root/go /root/go/bin

RUN /usr/local/bin/install.sh && /usr/local/bin/ssh_setup.sh

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]

COPY config/subfinder/provider-config.yaml /root/.config/subfinder/provider-config.yaml

WORKDIR /app

VOLUME ["/app/output", "/app/domains", "/app/workflows", "/app/wordlists"]
