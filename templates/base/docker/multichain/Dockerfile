FROM ubuntu:22.04

# MultiChain 2.3.3 — permissioned blockchain for agent identity & access control
# No cryptocurrency, no smart contracts needed — just data streams + permissions

ARG MULTICHAIN_VERSION=2.3.3
ARG TARGETARCH=amd64

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install MultiChain
RUN wget -q "https://www.multichain.com/download/multichain-${MULTICHAIN_VERSION}-linux-${TARGETARCH}.tar.gz" \
    -O /tmp/multichain.tar.gz \
    && tar xzf /tmp/multichain.tar.gz -C /tmp \
    && cp /tmp/multichain-${MULTICHAIN_VERSION}*/multichain* /usr/local/bin/ \
    && rm -rf /tmp/multichain*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME /root/.multichain
EXPOSE 4730 4731

ENV CHAIN_NAME=agi-memory-chain
ENV RPC_PORT=4730
ENV NETWORK_PORT=4731

ENTRYPOINT ["/entrypoint.sh"]
