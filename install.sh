#!/bin/sh
set -e

# Adiciona ao profile para persistir
echo "export PDCP_API_KEY=$PDCP_API_KEY" >> /etc/profile
echo "export GITHUB_TOKEN=$GITHUB_TOKEN" >> /etc/profile


# Instala OpenSSH Server e utilitários básicos
apt-get update && \
apt-get install -y --no-install-recommends openssh-server ca-certificates && \
rm -rf /var/lib/apt/lists/*

## Instala Utilitários básicos
apt-get update && apt-get install -y wget git unzip curl && rm -rf /var/lib/apt/lists/*

# Instala Go 1.25.1
rm -rf /usr/local/go && wget https://go.dev/dl/go1.25.1.linux-amd64.tar.gz -O /tmp/go1.25.1.tar.gz && \
tar -C /usr/local -xzf /tmp/go1.25.1.tar.gz && \
rm /tmp/go1.25.1.tar.gz

# Configura variáveis de ambiente do Go
export GOROOT=/usr/local/go
export GOPATH=/root/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

# Configurações de Localidade
export LC_ALL=C
export LANG=C.UTF-8
echo 'export LC_ALL=C' >> ~/.bashrc

# Adiciona ao profile para persistir
echo "export GOROOT=/usr/local/go" >> /etc/profile
echo "export GOPATH=/root/go" >> /etc/profile
echo "export PATH=\$PATH:\$GOROOT/bin:\$GOPATH/bin" >> /etc/profile

# Cria diretório GOPATH
mkdir -p $GOPATH

# Instala Python 3 e pip
apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*


## Tools Installation

# Instala jq
apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Instala awk
apt-get update && apt-get install -y gawk && rm -rf /var/lib/apt/lists/*

# Instala tee
apt-get update && apt-get install -y coreutils && rm -rf /var/lib/apt/lists/*

# Instala parallel
apt-get update && apt-get install -y parallel && rm -rf /var/lib/apt/lists/*

# Instala o anew
go install -v github.com/tomnomnom/anew@latest
cp /root/go/bin/anew /usr/local/bin/anew


## Subdomain Enumeration Tools

# Instala subfinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
cp /root/go/bin/subfinder /usr/local/bin/subfinder

# Instala chaos
go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest
cp /root/go/bin/chaos /usr/local/bin/chaos

# Instala github-subdomains
go install github.com/gwen001/github-subdomains@latest
cp /root/go/bin/github-subdomains /usr/local/bin/github-subdomains

# Instala ammass
CGO_ENABLED=0 go install -v github.com/owasp-amass/amass/v5/cmd/amass@main
cp /root/go/bin/amass /usr/local/bin/amass


# Instala httpx
pip uninstall 'httpx[cli]'
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
cp /root/go/bin/httpx /usr/local/bin/httpx

# Instala o dnsx
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
cp /root/go/bin/dnsx /usr/local/bin/dnsx

# Instala o nuclei
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
cp /root/go/bin/nuclei /usr/local/bin/nuclei
nuclei -update-templates

# Instala o subjs
go install -v github.com/lc/subjs@latest
cp /root/go/bin/subjs /usr/local/bin/subjs

# Instala o anti-burl
wget https://raw.githubusercontent.com/tomnomnom/hacks/master/anti-burl/main.go -O /tmp/anti-burl.go
# Build directly to /usr/local/bin and make executable (GOPATH copy may not exist)
go build -o /usr/local/bin/anti-burl /tmp/anti-burl.go
chmod +x /usr/local/bin/anti-burl
rm /tmp/anti-burl.go

# Instala Linkfinder
git clone https://github.com/GerbenJavado/LinkFinder.git /opt/LinkFinder
pip3 install -r /opt/LinkFinder/requirements.txt
chmod +x /opt/LinkFinder/linkfinder.py
ln -s /opt/LinkFinder/linkfinder.py /usr/local/bin/linkfinder

# Instala Collector do Bug-Bounty-Toolz
mkdir -p /opt/Bug-Bounty-Toolz
wget https://raw.githubusercontent.com/KingOfBugbounty/Bug-Bounty-Toolz/master/collector.py -O /opt/Bug-Bounty-Toolz/collector.py
chmod +x /opt/Bug-Bounty-Toolz/collector.py
ln -s /opt/Bug-Bounty-Toolz/collector.py /usr/local/bin/linkFinderCollector

# Instala o Rayder
go install github.com/devanshbatham/rayder@v0.0.4
cp /root/go/bin/rayder /usr/local/bin/rayder

