#!/bin/bash
set -e

CHAIN_NAME="${CHAIN_NAME:-agi-memory-chain}"
RPC_PORT="${RPC_PORT:-4730}"
NETWORK_PORT="${NETWORK_PORT:-4731}"
RPC_USER="${RPC_USER:-agiadmin}"
RPC_PASS="${RPC_PASS:-agipass123}"

# Check if chain already exists
if [ ! -d "/root/.multichain/${CHAIN_NAME}" ]; then
    echo "Creating new blockchain: ${CHAIN_NAME}"
    multichain-util create "${CHAIN_NAME}" \
        -default-network-port="${NETWORK_PORT}" \
        -default-rpc-port="${RPC_PORT}" \
        -anyone-can-connect=true \
        -anyone-can-send=true \
        -anyone-can-receive=true \
        -anyone-can-mine=true

    # Configure RPC access
    cat > "/root/.multichain/${CHAIN_NAME}/multichain.conf" <<EOF
rpcuser=${RPC_USER}
rpcpassword=${RPC_PASS}
rpcallowip=0.0.0.0/0
rpcport=${RPC_PORT}
EOF

    echo "Blockchain ${CHAIN_NAME} created."
else
    echo "Using existing blockchain: ${CHAIN_NAME}"
fi

echo "Starting MultiChain daemon on port ${RPC_PORT}..."
exec multichaind "${CHAIN_NAME}" -daemon=0 -rpcallowip=0.0.0.0/0
