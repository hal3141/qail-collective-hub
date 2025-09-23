#!/bin/bash
SHARE_DIR="$HOME/qail-datahub"

# Ensure Samba installed
if ! command -v smbd >/dev/null 2>&1; then
  echo "Installing Samba..."
  sudo apt install samba -y
fi

# Create directory if not exists
mkdir -p "$SHARE_DIR"

# Restart Samba
sudo systemctl restart smbd
echo "Data Hub shared at: smb://$(hostname -I | awk '{print $1}')/datahub"
