#!/bin/bash
HOST_IP="192.168.1.101"
MOUNT_POINT="/home/Desktop/qail-collective-hub"
USER="YOURUSER"
PASS="YOURPASS"

mkdir -p "$MOUNT_POINT"

# Mount Samba share
sudo mount -t cifs //$HOST_IP/datahub "$MOUNT_POINT" -o username=$USER,password=$PASS

cd "$MOUNT_POINT"
python3 app.py --host=0.0.0.0 --port=5000
