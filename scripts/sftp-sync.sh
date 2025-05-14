#!/usr/bin/env bash
set -eu

# Get name of machine
SELF_HOSTNAME=$(hostname)
SELF_IP=$(hostname -I | awk '{print $2}')  # Get IP
KEY_PATH="/home/vagrant/.ssh/id_ed25519"

# Path to temporary file
TMP_FILE="/tmp/${SELF_HOSTNAME}_$(date +'%Y%m%d_%H%M%S').txt"
echo "Created by ${SELF_HOSTNAME} at $(date)" > "$TMP_FILE"

# IP array of other machines 
TARGETS=("192.168.56.101" "192.168.56.102" "192.168.56.103")
for IP in "${TARGETS[@]}"; do
  if [[ "$IP" != "$SELF_IP" ]]; then
    echo "[INFO] Sending to $IP"
    sftp -i "$KEY_PATH" -o StrictHostKeyChecking=no -b - sftpuser@"$IP" <<EOF
cd uploads
put $TMP_FILE
bye
EOF
  fi
done

# Delete this temporary file
rm -f "$TMP_FILE"